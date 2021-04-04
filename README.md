
<h1 align="center">
  <br>
  LoopTrader
  <br>
</h1>

<h4 align="center">An extensible options trading bot built on top of Python.</h4>

<p align="center">
  <a href="#key-features">Key Features</a> •
  <a href="#how-to-use">How To Use</a> •
  <a href="#license">License</a>
</p>

## Key Features

The goal for LoopTrader is to provide a flexible engine for running one or more option trading strategies in real-time against provided broker API's. The Key Features include:

* Simple to setup and run multiple trading bots
* Extensibility for various brokers, trading strategies, and logging patterns
* Local storage for trades and orders

## How To Use

To clone and run this application, you'll need [Git](https://git-scm.com) installed on your computer. From your command line:

```bash
# Clone this repository
$ git clone https://github.com/pattertj/LoopTrader/

# Go into the repository
$ cd LoopTrader

# Run main.py
$ python main.py
```

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

The Broker abstract class represents the base class for concrete Broker implementations. This includes basic information about connecting to the Broker and Abstract Methods for acting on the Broker. Today LoopTrader includes support for:

* [TD Ameritrade](https://developer.tdameritrade.com/apis)

### Database

The Database abstract class provides the scaffolding CRUD operations for various concrete local storage implementations. Currently this portion is not functional but the plan is to initially provide support for [Sqlite](https://sqlite.org/index.html).

### Strategy

The Strategy abstract class is the base for all Strategies implemented in LoopTrader. Most of the logic within LoopTrader exists within the concrete Strategies to dertermine when to open and close positions. The first concrete strategy in progress is CashSecuredPuts selected by target Delta.

## How To Add Custom Strategies

Custom Strategies can be added by creating a new class inheriting from Strategy and Component and implementing the required abstract methods. This pattern will allow you communicate with the bot in a standard way and keep strategies plug-and-play.

## How To Add Different Brokers

New Brokers can be added by creating a new class inheriting from Broker and Component and implementing the required abstract methods. This pattern will allow you communicate with the bot in a standard way and keep Brokers plug-and-play.

## License

GNU General Public License v3.0

---

> GitHub [@pattertj](https://github.com/pattertj) &nbsp;&middot;&nbsp;
