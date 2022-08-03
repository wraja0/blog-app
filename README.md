## Mini Project 2

A blogging application built with flask and SQLAlchemy where unregistered users can view blog posts. Includes a public home and about page. Users can register for a new account with their email. Passwords are hashed and stored securly in a postgres server. User login status and other redundant data persist through the application using JSON web tokens. Uses pytest library for testing.

[![linting: pylint](https://img.shields.io/badge/linting-pylint-yellowgreen)](https://github.com/PyCQA/pylint)

## Visuals
![Screenshot of home page](https://i.imgur.com/dRk8IzM.png)
![Screenshot of about page](https://i.imgur.com/GBvPA4Z.png)
![Screenshot of register page](https://i.imgur.com/VGwdGjR.png)


## Installation

1. Clone this repository down to your machine

2. Use 'conda env create -f environment.yml' to create your virtual environment

If you do not wish to use conda for your virtual environment you will need to install the packages in the environment.env file using pip or similar python package manager

## Usage

Deploy your application using your favorite deployment platform. All users are able to view published posts. However only registered users can create posts. Registered users can also edit and delete their own posts. Users can register for free and are promptly redirected to login. If a user is an admin, when first logging in they can view all registered usernames and their respective email address. 

## Roadmap

Comments and tags coming sooon !

## Support


## Contributing

## Authors and acknowledgment


## License


## Project status
