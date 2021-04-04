
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

* Simple to setup and run multiple trading bots
* Extensibility for various brokers, trading strategies, and logging patterns

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

LoopTrader is built on top of the latest version of Python and implements two main patterns: Mediator and Strategy

## How To Add Custom Strategies

Custom strategies can be added by creating a new class inheriting from Strategy and Component and implementing the required abstract method. This pattern will allow you communicate with the bot in a standard way and keep strategies plug-and-play.

## How To Add Different Brokers

## License

GNU General Public License v3.0

---

> GitHub [@pattertj](https://github.com/pattertj) &nbsp;&middot;&nbsp;
