# Subrosa


[![Build Status](https://travis-ci.org/exaroth/subrosa.png?branch=master)](https://travis-ci.org/exaroth/subrosa)



Subrosa is simple and elegant blogging platform written in Python, meant to be easy to use and deploy. Features:

* Builtin markdown editor
* Imgur integration for uploading images
* Autogenerated table of contents for each article
* Code highlighting via Pygments
* Semirandomized gallery
* Comments via disqus
* Simple projects page
* Responsive design


## Installation

### Including Images

If you want additional graphics on your index page simply drop them into /uploads folder, this can be in any common format you like: jpg, png and gif. The files are:

	* bg -- used as a background image, it will automatically resize to match the container.
	* logo -- If instead of plain title you want to have customized logo.
	* portrait -- Your portrait, this image will show up next to your posts as well as on index page.

Additionally if you want to have favicon on your page, drop file named favicon.ico into /uploads.

Note: None of these images are mandatory.

### Basic configuration

The configuration file is named subrosa.conf and you can find it inside main folder of the repository, The only things to configure are:

* SITE_TITLE -- Self explanatory
* SECRET_KEY -- This can be anything you like as long as you change it, its used for encrypting passwords and other security related stuff.
* DATABASE -- select database type you want to use with Subrosa, available types are sqlite, postgresql and mysql.
* DATABASE_NAME -- name of the database to be used, note you have to create it yourself.
* USERNAME/PASSWORD -- Credentials used when connecting to database, used only with mysql and postgresql.

NOTE: Database configuration is automatically  generated when using Subrosa with Heroku.

NOTE: If you want more configuration options you can find detailed config file inside main folder(default_config.py).

### Deployment


At this moment the best solution for deployment is to use Heroku cloud, with this setting Subrosa doesn't require any database configuration, and hey, it's free.

#### Heroku Installation

Instructions below assume you have Heroku toolbelt installed on your system (if not create account on Heroku, visit [https://toolbelt.heroku.com/](https://toolbelt.heroku.com/) and install it).

1. Clone the repository
```
git clone https://github.com/exaroth/subrosa.git && cd subrosa
```
2. Create heroku app
```
heroku create --stack cedar <name_of_your_app>
```
3. Add postgresql database and promote it.


```
heroku addons:add heroku-postgresql
```


get info about installed db


```shell
heroku pg:info
```


Which should return something like:


```shell
HEROKU_POSTGRESQL_LAVENDER_URL <== Database name
Plan:        Dev
Status:      available
```


