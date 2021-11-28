
<h1 align="center">
  <br>
  <a href="https://github.com/pattertj/LoopTrader/"><img src="https://i.ibb.co/KqRpvVN/stock-exchange-app-2.png" alt="LoopTrader" width="200"></a><br>
  LoopTrader
  <br>
</h1>

<p align="center">
<a href="https://github.com/pattertj/LoopTrader/commits/main"><img src="https://img.shields.io/github/last-commit/pattertj/LoopTrader"></a> 
  <a href="https://github.com/pattertj/LoopTrader/actions/workflows/python-app.yml"><img src="https://img.shields.io/github/workflow/status/pattertj/looptrader/Build?style=flat"></a> 
  <a href="https://github.com/pattertj/LoopTrader/network/members"><img src="https://img.shields.io/github/forks/pattertj/LoopTrader?style=flat"></a> 
  <a href="https://github.com/pattertj/LoopTrader/stargazers"><img src="https://img.shields.io/github/stars/pattertj/LoopTrader?style=flat"></a> 
  <a href="https://github.com/pattertj/LoopTrader/blob/main/LICENSE"><img src="https://img.shields.io/github/license/pattertj/LoopTrader?style=flat"></a>
</p>

<h4 align="center">An extensible options trading bot built on top of Python.</h4>

<p align="center">
  <a href="#description">Description</a> •
  <a href="#installation">Installation</a> •
  <a href="#usage">Usage</a> •
  <a href="#contributing">Contributing</a> •
  <a href="#license">License</a>
</p>

## Description
The goal for LoopTrader is to provide a flexible engine for running one or more option trading strategies in real-time against provided broker API's. The Key Features include:

* Simple to setup and run multiple trading bots
* Extensibility for various brokers, trading strategies, and logging patterns
* Local storage for trades and orders *(In Progress)*
* Support for notifications and interactions through tools like Telegram  

<b>LoopTrader is very much a work in progress and is currently not feature complete. See the [Issues](https://github.com/pattertj/LoopTrader/issues) for what remains open, or to make a suggestion.</b>

## Installation
Getting up and running with LoopTrader is just a few commands:

    # Clone LoopTrader
    git clone https://github.com/pattertj/LoopTrader.git

    # Install dependencies
    pipenv install --dev

    # Setup pre-commit and pre-push hooks
    pipenv run pre-commit install -t pre-commit
    pipenv run pre-commit install -t pre-push

More detailed instructions on specific components can be found in the [wiki](https://github.com/pattertj/LoopTrader/wiki).

## Usage
Currently all configuration of LoopTrader is done in the code when creating the bot in [main.py](https://github.com/pattertj/LoopTrader/blob/looptrader/__main__.py), the [.env](https://github.com/pattertj/LoopTrader/blob/looptrader/sample.env), and [config.yaml](https://github.com/pattertj/LoopTrader/blob/looptrader/sample.config.yaml) file. A sample .env and .yaml file are provided, but should be renamed to ".env" and "config.yaml" respectively, with the configuration variables populated.

## Contributing
### Start contributing right now:

#### Open an issue
If you've found a problem, you can open an [issue](https://github.com/pattertj/LoopTrader/issues/new)!

#### Solve an issue
If you have a solution to one of the open issues, you will need to fork the repository and submit a pull request. 

## Credits
Big thanks to the great people on Discord. You know who you are.

## License

GNU General Public License v3.0

---

> GitHub [@pattertj](https://github.com/pattertj)
