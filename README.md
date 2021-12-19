# alpaca-py-ms
**This repo is a work in progress - not yet complete**

Python microservice for interacting with the Alpaca Trading API. The intention of this project is to be a single service running alongside others making up a complete trading system. It seeks to accomplish the following:
- Manage connection with Alpaca websocket client, publish order updates for use by other microservices (portfolio manager, etc)
- Handle minute bars from Alpaca websocket, aggregate the data and populate longer duration bars in Alpaca MarketStore
  - https://github.com/alpacahq/marketstore
  - https://github.com/alpacahq/pymarketstore



### Environment variables summary
| Var                     | Type   | Description                                               |
|-------------------------|--------|-----------------------------------------------------------|
| ALPACA_MS_LOG_DIRECTORY | string | Directory to write run logs and recorded message binaries |
| APCA_RUN_MODE           | string | "paper" or "live" (default is paper)                      |
| APCA_API_KEY_ID         | string | Alpaca API key (overrides alpaca.yml)                     |
| APCA_API_SECRET_KEY     | string | Alpaca secret API key (overrides alpaca.yml)              |
| APCA_API_BASE_URL       | string | Alpaca base URL                                           |
