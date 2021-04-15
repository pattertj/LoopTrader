
<h1 align="center">
  <br>
  <a href="https://github.com/pattertj/LoopTrader/"><img src="https://i.ibb.co/KqRpvVN/stock-exchange-app-2.png" alt="LoopTrader" width="200"></a><br>
  LoopTrader
  <br>
</h1>

<p align="center">
<img src="https://img.shields.io/github/issues/pattertj/LoopTrader?style=for-the-badge"> <img src="https://img.shields.io/github/forks/pattertj/LoopTrader?style=for-the-badge"> <img src="https://img.shields.io/github/stars/pattertj/LoopTrader?style=for-the-badge"> <img src="https://img.shields.io/github/license/pattertj/LoopTrader?style=for-the-badge">
</p>

<h4 align="center">An extensible options trading bot built on top of Python.</h4>

<p align="center">
  <a href="#key-features">Key Features</a> •
  <a href="#how-to-use">How To Use</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#license">License</a>
</p>

## Key Features

The goal for LoopTrader is to provide a flexible engine for running one or more option trading strategies in real-time against provided broker API's. The Key Features include:

* Simple to setup and run multiple trading bots
* Extensibility for various brokers, trading strategies, and logging patterns
* Local storage for trades and orders
* Support for notifications and interactions through tools like Telegram  

LoopTrdaer is very much a work in progress and is currently not feature complete. See the [Issues](https://github.com/pattertj/LoopTrader/issues) for what remains open, or to make a suggestion.

## How To Use

Running LoopTrader does require some development experience. Configuring LoopTrader for various strategies, brokers, and enabling notifiers all take some editing of LoopTrader to work.

### Configuring TD Ameritrade/ToS

Connecting to TD Ameritrade from LoopTrader leverages the [td-ameritrade-python-api](https://github.com/areed1192/td-ameritrade-python-api) project. [Installation](https://github.com/areed1192/td-ameritrade-python-api#installation) and the [Authentication Workflow](https://github.com/areed1192/td-ameritrade-python-api#authentication-workflow) should be completed before using LoopTrade with TD Ameritrade. Additionally, you should be setup with a [TD Ameritrade Developer Account](https://developer.tdameritrade.com/apis)

The required configuration parameters should be setup in LoopTrader's [.env](https://github.com/pattertj/LoopTrader/blob/main/.env) file using the documented Environment Variables.

    # TD Ameritrade Broker Variables
    TDAMERITRADE_CLIENT_ID= ""
    TDAMERITRADE_ACCOUNT_NUMBER= ""
    REDIRECT_URL= ""
    CREDENTIALS_PATH= ""

#### How To Add Different Brokers

New Brokers can be added by creating a new class inheriting from Broker and Component and implementing the required abstract methods. This pattern will allow you communicate with the Bot in a standard way and keep Brokers plug-and-play.

### Configuring Telegram

The Telegram notifier uses the [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) for communicating with Telegram. For personal use, you must [install](https://github.com/python-telegram-bot/python-telegram-bot#installing) the module and create a [new bot](https://core.telegram.org/bots#6-botfather) through [@BotFather](https://t.me/botfather).

The required configuration parameters should be setup in LoopTrader's [.env](https://github.com/pattertj/LoopTrader/blob/main/.env) file using the documented Environment Variables.

    # Telegram Notifier Variables
    TELEGRAM_TOKEN= ""
    TELEGRAM_CHATID= ""

### Configuring Sqlite3

Sqlite3 is still in development.

### Configuring Strategies

Strategies are still in development.

#### How To Add Custom Strategies

Custom Strategies can be added by creating a new class inheriting from Strategy and Component and implementing the required abstract methods. This pattern will allow you communicate with the bot in a standard way and keep strategies plug-and-play.

## Architecture

LoopTrader is built on top of the latest version of Python and implements two main patterns: [Mediator](https://sourcemaking.com/design_patterns/mediator) and [Strategy](https://sourcemaking.com/design_patterns/strategy)

The Mediator pattern allow us to maintain independant components for the Broker API, Strategy, and Local DB's. This let's the user pick and choose the components to include in their Bot.

The Strategy pattern allows us to develop multiple implementations of trading strategies for the bot to execute.

The core components of LoopTrader are outlined below. For anyone interested in extending LoopTrader to a new Broker or Strategy, take a look at main.py for how to set up your Bot and the sections below for how to extend the components.

### Component

The Component abstract class is the base class for our pieces of a Bot, it should be on all classes that intend to be processed by the Bot.

### Mediator

The Mediator abstract class is represented in it's concrete form as the Bot, it is the core object for coordinating the Component pieces, and handling the looping of Strategies.

### Broker

The Broker abstract class represents the base class for concrete Broker implementations. This includes basic information about connecting to the Broker and Abstract Methods for acting on the Broker.

### Notifier

The Notifier abstract class is how we can receive notifications and interact with our bot.

### Database

The Database abstract class provides the scaffolding CRUD operations for various concrete local storage implementations. Currently this portion is not functional but the plan is to initially provide support for [Sqlite](https://sqlite.org/index.html).

### Strategy

The Strategy abstract class is the base for all Strategies implemented in LoopTrader. Most of the logic within LoopTrader exists within the concrete Strategies to dertermine when to open and close positions. The first concrete strategy in progress is CashSecuredPuts selected by target Delta.

## License

GNU General Public License v3.0

---

> GitHub [@pattertj](https://github.com/pattertj)
