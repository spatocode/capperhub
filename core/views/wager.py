import pytz
from datetime import datetime, timedelta
from django.conf import settings
from django.db.models import Count, Q
from django.core.cache import cache
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from rest_framework.decorators import permission_classes
from rest_framework import authentication, permissions
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from core.permissions import IsOwnerOrReadOnly
from core.serializers import (
    PlaySerializer, UserAccountSerializer, SubscriptionSerializer,
    SportsWagerSerializer, TransactionSerializer, SportsGameSerializer, TeamSerializer,
    CompetitionSerializer, SportSerializer, MarketSerializer, PlaySlipSerializer
)
from core.models.user import UserAccount
from core.models.transaction import Transaction
from core.models.play import Play, PlaySlip
from core.models.wager import SportsWager, SportsWagerChallenge
from core.models.games import SportsGame, Sport, Competition, Team, Market
from core.models.subscription import Subscription
from core.filters import PlayFilterSet, UserAccountFilterSet, SubscriptionFilterSet, SportsWagerFilterSet, SportsGameFilterSet
from core.exceptions import SubscriptionError, InsuficientFundError, NotFoundError, ForbiddenError, PermissionDeniedError
from core.shared.helper import sync_records, sync_subscriptions, notify_subscribers


class CsrfExemptSessionAuthentication(authentication.SessionAuthentication):
    def enforce_csrf(self, request):
        return


@permission_classes((permissions.IsAuthenticated, IsOwnerOrReadOnly))
class SportsWagerAPIView(ModelViewSet):
    filter_class = SportsWagerFilterSet

    @method_decorator(ratelimit(key='ip', rate=f'{settings.DEFAULT_RATE_LIMIT}/m', method='GET'))
    def get_wagers(self, request):
        filters = Q(backer=request.user.useraccount.id) | Q(layer=request.user.useraccount.id)
        filterset = self.filter_class(
            data=request.query_params,
            queryset=SportsWager.objects.filter(filters).order_by("-placed_time")
        )
        serializer = SportsWagerSerializer(filterset.qs, many=True)

        return Response(serializer.data)

    @method_decorator(ratelimit(key='ip', rate=f'{settings.DEFAULT_RATE_LIMIT}/m', method='GET'))
    def get_game_wagers(self, request, pk=None):
        try:
            games = SportsGame.objects.get(pk=pk)
        except SportsGame.DoesNotExist:
            raise NotFoundError(detail="Game not found")
        queryset = games.wagers.all()
        serializer = SportsWagerSerializer(queryset, many=True)

        return Response(serializer.data)

    @method_decorator(ratelimit(key='ip', rate=f'{settings.DEFAULT_RATE_LIMIT}/m', method='GET'))
    def place_wager(self, request):
        data = request.data
        self.check_object_permissions(request, data.get('backer'))
        if request.user.useraccount.wallet.balance < int(data.get("stake")):
            raise InsuficientFundError(detail="You don't have sufficient fund to stake")
        serializer = SportsWagerSerializer(data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        sports_wager = serializer.save()
        game_serializer = SportsGameSerializer(sports_wager.game)
        useraccount_wallet = request.user.useraccount.wallet
        useraccount_wallet.withheld = useraccount_wallet.withheld + int(data.get("stake"))
        useraccount_wallet.balance = useraccount_wallet.balance - int(data.get("stake"))
        useraccount_wallet.save()
        if data.get("opponent"):
            self.handle_wager_invitation(sports_wager, requestee=data.get("opponent"), requestor=request.user.useraccount)
        return Response({
            'message': 'Wager Challenge Created Successfully',
            'data': serializer.data
        })

    @method_decorator(ratelimit(key='ip', rate=f'{settings.DEFAULT_RATE_LIMIT}/m', method='GET'))
    def match_wager(self, request):
        # TODO: Send websocket notifications
        try:
            sports_wager = SportsWager.objects.select_related("backer", "game", "transaction").get(pk=request.data.get("wager"))
        except SportsWager.DoesNotExist:
            raise NotFoundError(detail="Wager not found")

        if request.user.useraccount.wallet.balance < sports_wager.stake:
            raise InsuficientFundError(detail="You don't have sufficient fund to stake")

        if sports_wager.game.result:
            raise ForbiddenError(detail="Game no longer available for wager")
        
        if sports_wager.matched:
            raise ForbiddenError(detail="Wager no longer available to play")

        if sports_wager.backer.id == request.user.useraccount.id:
            raise PermissionDeniedError(detail="Action not permitted")

        serializer = sync_records(
            sports_wager,
            request.user.useraccount,
            layer_option=request.data.get("layer_option")
        )
        return Response({
            'message': 'Wager matched successfully',
            'data': serializer.data
        })

    def handle_wager_invitation(self, wager, requestee=None, requestor=None):
        # TODO: send SMS invitation with a generated link to signup, fund account
        # and accept invitation.
        # Send web socket notification after inviting a registered user
        user = UserAccount.objects.get(user__username=requestee)
        if requestor.id == user.id:
            raise PermissionDeniedError(detail="Action not permitted")
        SportsWagerChallenge.objects.create(
            wager=wager,
            requestor=requestor,
            requestee=user
        )


@permission_classes((permissions.AllowAny,))
class P2PSportsGameAPIView(APIView):
    filter_class = SportsGameFilterSet

    @method_decorator(ratelimit(key='ip', rate=f'{settings.DEFAULT_RATE_LIMIT}/m', method='GET'))
    def get(self, request):
        filterset = self.filter_class(
            data=request.query_params,
            queryset=SportsGame.objects.all()
            .annotate(wager_count=Count("wagers"))
        )
        serializer = SportsGameSerializer(filterset.qs, many=True)

        return Response(serializer.data)


@permission_classes((permissions.IsAuthenticated, IsOwnerOrReadOnly))
class SportsWagerChallengeAPIView(APIView):
    @method_decorator(ratelimit(key='ip', rate=f'{settings.DEFAULT_RATE_LIMIT}/m', method='GET'))
    def get(self, request):
        """Get wager challenges"""
        # TODO: Add invitation date_initialized to the returned SportsWager queryset
        # Find better ways to optimize this operation
        wager_list = [challenge.wager.id for challenge in SportsWagerChallenge.objects.filter(
            requestee=request.user.useraccount.id,
            accepted=False
        ).select_related("wager").order_by("-date_initialized")]
        queryset = SportsWager.objects.filter(id__in=wager_list)
        serializer = SportsWagerSerializer(
            queryset, many=True
        )

        return Response(serializer.data)

    @method_decorator(ratelimit(key='ip', rate=f'{settings.DEFAULT_RATE_LIMIT}/m', method='POST'))    
    def post(self, request):
        """Accept wager challenges"""
        # TODO: Send websocket notifications
        try:
            queryset = SportsWager.objects.select_related("backer").get(
                id=request.data.get("wager")
            )
        except SportsWager.DoesNotExist:
            raise NotFoundError(detail="Wager not found")

        if request.user.useraccount.wallet.balance < queryset.stake:
            raise InsuficientFundError(detail="You don't have sufficient fund to stake")

        try:
            invitation = queryset.invitation.get(requestee=request.user.useraccount)
        except queryset.invitation.DoesNotExist:
            raise PermissionDeniedError(detail="Action not permitted")
        
        if queryset.backer.id == request.user.useraccount.id:
            raise PermissionDeniedError(detail="Action not permitted")

        if queryset.matched:
            raise ForbiddenError(detail="Wager no longer available to play")

        invitation.accepted = True
        invitation.save()

        serializer = sync_records(
            queryset,
            request.user.useraccount,
            layer_option=request.data.get("layer_option")
        )

        return Response({
            "message": "Challenge accepted",
            "data": serializer.data
        })


@permission_classes((permissions.IsAuthenticated,))
class TeamAPIView(ModelViewSet):
    serializer_class = TeamSerializer

    @method_decorator(ratelimit(key='ip', rate=f'{settings.DEFAULT_RATE_LIMIT}/m', method='GET'))
    def get_queryset(self):
        cache_key = 'team'
        if cache_key in cache:
            data = cache.get(cache_key)
        else:
            queryset = Team.objects.filter(
                competition__name=self.request.query_params.get('competition')
            )
            data = queryset
            cache.set(cache_key, data, timeout=settings.CACHE_TTL)
        return data


@permission_classes((permissions.IsAuthenticated,))
class SportAPIView(ModelViewSet):
    serializer_class = SportSerializer

    @method_decorator(ratelimit(key='ip', rate=f'{settings.DEFAULT_RATE_LIMIT}/m', method='GET'))
    def get_queryset(self):
        cache_key = 'sport'
        if cache_key in cache:
            data = cache.get(cache_key)
        else:
            queryset = Sport.objects.filter()
            data = queryset
            cache.set(cache_key, data, timeout=settings.CACHE_TTL)
        return data


@permission_classes((permissions.IsAuthenticated,))
class CompetitionAPIView(ModelViewSet):
    serializer_class = CompetitionSerializer

    @method_decorator(ratelimit(key='ip', rate=f'{settings.DEFAULT_RATE_LIMIT}/m', method='GET'))
    def get_queryset(self):
        cache_key = 'competition'
        if cache_key in cache:
            data = cache.get(cache_key)
        else:
            queryset = Competition.objects.filter(
                sport__name=self.request.query_params.get('sport')
            )
            data = queryset
            cache.set(cache_key, data, timeout=settings.CACHE_TTL)
        return data


@permission_classes((permissions.IsAuthenticated,))
class MarketAPIView(ModelViewSet):
    serializer_class = MarketSerializer

    @method_decorator(ratelimit(key='ip', rate=f'{settings.DEFAULT_RATE_LIMIT}/m', method='GET'))
    def get_queryset(self):
        cache_key = 'market'
        if cache_key in cache:
            data = cache.get(cache_key)
        else:
            queryset = Market.objects.filter(
                sport__name=self.request.query_params.get('sport')
            )
            data = queryset
            cache.set(cache_key, data, timeout=settings.CACHE_TTL)
            return data
