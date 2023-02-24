# Predishun




## TODOS

[] Redesign dashboard.

[x] Change tips model and all occurences to play

[] Add ability to send plays through SMS, EMAIL and TELEGRAM. Consider the cost of integrating any service to the system. If the consideration doesn't work out, better allow an exclusive support of those platforms only by premium users.

[] If websocket support would take lots of time to integrate, consider making a cached request on each refresh to few important APIs like subscribers and tips.

[x] Create p2p betting system. A user can place a bet with another user on the outcome of an event(not exclusive to sports. ChatGPT might be considered to help to decide the outcome of the event if no other means are found). This would happen when a user send an SMS game request to a another user with details of the event involved. The user can accept by clicking the accept link sent with the SMS, to accept and register. A user can also stake and predict on an event and another user can counter his stake with the same amount of stake.

[] Users should not rely on typing sports teams and league themselves. There should be a json data of such info on the UI.

[] Update plays with game result to create analysis of tipsters performance.

[] Handle email and phone verification on signup

[] Handle email and phone verification on change

[] Make sure the datetime in DB are timezone aware

[] Support responsive UI.

[] Add tests



## Future Roadmap
- Evolve to develop a fintech product for recharging airtimes and data, making transfers(even using whatsapp, twitter or telagram API integration).
