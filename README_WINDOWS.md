# Makeability Lab Website
The Makeability Lab is a an HCI/Ubicomp research lab at the University of Washington directed by Professor Jon Froehlich. Founded in 2012 by Froehlich and students, the Makeability Lab focuses on designing and studying novel interactive experiences that cross between bits and atoms—the virtual and the physical—and back again to confront some of the world's greatest challenges in environmental sustainability, health and wellness, education, and universal accessibility. 

This repository contains the Makeability Lab's website, which is written in Django (backend) and Bootstrap/Javascript (frontend).

# Dev Prereqs
While the instructions below walk you through a step-by-step process to configure your machine for developing the Makeability Lab website, here's a summary of the tools we use:
- Docker
- PyCharm
- Git

Use Windows PowerShell to run the following set-up commands in order to ensure the correct syntax.

# Docker Installation
1. If you don't have Docker yet, you can download it [here](https://store.docker.com/search?type=edition&offering=community). We use the Community Edition. Open up the application. When prompted to check whether to use Windows containers instead of Linux containers, do not check the box. Run `docker version` to make sure that it is running. 
  If you previously installed Docker, please navigate to the Docker settings, in the window go to the Reset tab and click "Restore Factory defaults". This will ensure that there will be no conflicts in allocating ports later on.

When first starting up Docker, navigate to the Docker icon in hidden icons and right-click to bring up settings. In settings, navigate to the "Shared Drives" tab and select the drive that you have cloned the git repository to. Click "Apply" and you will be prompted to enter the password for your machine.
[![https://gyazo.com/16d374eeadcd0cc550b8ab17f4bcbe5f](https://i.gyazo.com/16d374eeadcd0cc550b8ab17f4bcbe5f.gif)](https://gyazo.com/16d374eeadcd0cc550b8ab17f4bcbe5f)

2. Before you clone the repository, run this command `git config --global core.autocrlf false` in the directory you will be cloning the repository to. Windows crlf is unrecognized in Linux, thus we must set this auto-conversion as false to prevent look-up errors.
3. Clone this repository using `git clone` and navigate to the project home directory using the `cd` command.
4. Build the docker images. Run `docker build . [-t] <tag>` to give your build a name (We recommend tagging it as `makelab_image` for easy access). This step takes a while the first time (~2-3 min). If you don't add a tag to your build in step 3, you can look at the last line of the build that says `Successfully built <tag>` to get your tag.
5. Open the interactive bash terminal using `docker run -ti -v ${pwd}/db:/code/db -v ${pwd}/media:/code/media --entrypoint=bash [tag]`
6. Create the local database. Run the following commands: `python3 manage.py makemigrations website` and `python3 manage.py migrate`. Type `exit` to leave the interactive terminal.
7. Create the superuser. Run `docker run -ti -v ${pwd}/db:/code/db -v ${pwd}/media:/code/media --entrypoint=python [tag] manage.py createsuperuser`.
8. Rebuild the docker images. Use `docker build . [-t] [tag]`
9. Run the local server using Docker. Use `docker run -p 8000:8000 -ti -v ${pwd}/db:/code/db -v ${pwd}/media:/code/media -v ${pwd}/website:/code/website [tag]` 
10. Open the development server in the web browser. This will be at `localhost:8000`.

After running the `docker run` command, you will not need to rebuild or rerun the Docker container after making changes. However, you will still need to refresh the webpage in order to see new updates. This development server will now persist even when you close down PowerShell. Thus, if you try to run the `docker run -p 8000:8000 -ti -v ${pwd}/db:/code/db -v ${pwd}/media:/code/media -v ${pwd}/website:/code/website [tag]` command again, you will receive the error:  `Error response from daemon: driver failed programming external connectivity on endpoint ecstatic_minsky (69ef6a6c62ca6b54bc81976758f03bf6e0c80362e3a9b7a8890714b4cc57d07f): Bind for 0.0.0.0:8000 failed: port is already allocated.`
### Sample setup:
```
# navigate to the directory you will be cloning the repository into
git config --global core.autocrlf false
git clone https://github.com/jonfroehlich/makeabilitylabwebsite.git
cd .\makeabilitylabwebsite\
docker build . -t makelab_image
docker run -ti -v ${pwd}/db:/code/db -v $(pwd)/media:/code/media --entrypoint=bash makelab_image
python3 manage.py makemigrations website
python3 manage.py migrate
exit
docker run -ti -v ${pwd}/db:/code/db -v ${pwd}/media:/code/media --entrypoint=python makelab_image manage.py createsuperuser
docker build . -t makelab_image
docker run -p 8000:8000 -ti -v ${pwd}/db:/code/db -v ${pwd}/media:/code/media -v ${pwd}/website:/code/website makelab_image
```
## Manual Installation (In the event that Docker fails to run)
Proceed to the manual installation instrucations [here](https://docs.google.com/document/d/1LJPSSZA0kLzUX34pq4TgYP406bGH_1JhBtFLEPax7a8/edit?usp=sharing)

## Setting up Docker in PyCharm (Optional)
We recommend using PyCharm as an IDE. Note that in order to configure PyCharm with Docker, you must have the professional version. Students can get this for free at: https://www.jetbrains.com/student/. If you configured the Docker server in the previous step, then you do not need to follow-through with this step. This will only make Pycharm recognize the existence of Docker-related commands and not return syntax errors in the IDE.

### IDE Configuration
1. Select 'Open New Project'. Select the root directory of this project for the file.
2. Go to Run > Edit Configurations. In the side window, go to Defaults > Docker > Dockerfile.
3. Click on the `...` by Server. Select the `Docker for [your OS here]` option. Click `OK` to finish.
4. Click on the `+` button in the upper-left corner to add a new configuration.
5. Set the name to be `makeabilitylabwebsite`, the Dockerfile to be `Dockerfile` with the drop-down menu, and the image tag to `pycharm`. Click `OK` to finish.
6. Select Run > Run 'makeabilitylabwebsite'.
7. Go to Pycharm > Preferences > Project Interpreter
8. Click on the Gear button to the right of the Project Interpreter. Select the `Add...` button.
9. Open the Docker option. The Image Name should be `pycharm:latest`. Click `OK` to finish.

### Configuring PyCharm to run the website server (optional)
You may choose to use either the Terminal or PyCharm to run the website server.

NOTE: If you haven't created a superuser yet, you will need to do so through terminal. Refer to Step 6 in the Docker Installation for more information.

1. Go to Run > Run 'makeabilitylabwebsite'. The initial setup for this might take a minute or so.
2. Go to the Docker toolbar. (This should pop up automatically on the bottom of your screen). Click on the dropdown menu for images. Press create container and select `pycharm:latest`. Set the Container name to be `pycharm-web-container`. 
3. Click on the `...` button by Bind Ports. Click the `+` button, and select the Host Port to be `8000` and the Container Port to be `8000`. Click OK to finish.
4. Click on the `...` button by Bind Ports. Click the `+` button, and select the Host path to be `database` and the Container path to be `/code/db`. (Windows users may need to switch the Container path to `\code\db`).
5. Click the `+` button again. Under Host path, click the `...` button. Select the media directory. Select the Container path to be `/code/media`. (Windows users may need to switch the Container path to `\code\media`).
6. Right click on `pycharm-web-container`. Click 'Start container' to run and 'Stop container' to stop the local server. (The attached consoles isn't interactive, so ctrl+c doesn't work here)


# Deploying to Production
The Makeability Lab website auto-deploys from GitHub to the department's Docker infrastructure using webhooks:
![webhooks_screenshot](https://github.com/jonfroehlich/makeabilitylabwebsite/blob/master/media/readme/webhooks_screenshot.png "Webhooks Screenshot") When we push code to github, the new code will auto-deploy to makeabilitylab-test. When we are ready to push changes to production, we need to do the following:
```
git tag <my version number>
git push --tags
```
This will cause that tag to deploy to production. 

## Versioning
We will using semantic versioning when adding tags to push to production. The table below gives instructions for how semantic labeling works. More information is available [here](https://docs.npmjs.com/getting-started/semantic-versioning).

The current version is `0.1.0`, since we are still in development. A history of all pushes to production can be accessed through the 'releases' tag on Github.

| Code Status    | Stage        | Rule             | Example # |
| -------------- | ------------ | ---------------- | --------- |
| First Release  | New Product  | Start with 1.0.0 | 1.0.0     |
| Bug fixes, other </br> minor changes  | Patch release | Increment the third digit | 1.0.1 |
| New Features that don't </br> break existing features  | Minor release | Increment the middle digit | 1.1.0 |
| Changes that break </br> backwards compatibility | Major release | Increment the first digit | 2.0.0 |

## Configuring the Production Server
The production server was configured largely by UW CSE's Jason Howe. Note that settings.py reads in a config.ini file to configure a connection to the PostgreSQL database. This config.ini file is *not* in git (for obvious reasons as it contains secret keys and passwords). Thus, Jason has setup a "volume mount" for this file so that the production Docker session can read that file.

## Debugging the Production Server
Currently, both makeabilitylab-test.cs.washington.edu and makeabilitylab.cs.washington.edu are logging to `/media/debug.log`. To access this, ssh into recycle.cs.washington.edu and cd to `/cse/web/research/makelab/www`. You should see the file there.

You can also view `buildlog.text`, `httpd-access.log`, and `httpd-error.log` at https://makeabilitylab-test.cs.washington.edu/logs/ and https://makeabilitylab.cs.washington.edu/logs/.

# Makeability Lab Data
There are two types of Makeability Lab data: (i) uploaded files like PDFs, PowerPoint files, images, etc. and (ii) data that goes into the database (SQLite in local dev, PostgreSQL on production).

## Uploaded Files
All data/files uploaded to the Makeability Lab website via the admin interface (e.g., talks, publications) goes into the `/media` folder. Although typically you will not ever need to manually access this folder (except, for example, to view the `debug.log`), you can do so by ssh'ing into recycle.cs.washington.edu and cd to `/cse/web/research/makelab/www`. This files area is being mapped into the `/media` folder. 

## Access to Production Database Server
The Makeability Lab website uses PostgreSQL on production, which is running on grabthar.cs.washington.edu. In the (extremely) rare instance that you need to access Postgres directly, you must do so via recycle.cs.washington.edu.

# Manual Installation
We strongly advise running the Docker-based installation since that's what the department mandates and you get an instantly configured dev environment for free. However, if you want the *pain* :) of manually installing all of the required libs, then this is how you should do it. The full step-by-step instructions for installation are [here](https://docs.google.com/document/d/149S_SHOzkJOhNHU4ENMU0YCbk-Vy92y5ZSTeCXG9Bhc/edit) (invite only for now).

## Requirements
* Python 3.51
* Pip 3
* Django 1.9
* ImageMagick
* ghostscript
* django_extensions (pip)
* Pillow (pip)
* Wand (pip)
* bibtex parser (pip)
* xmltodict (pip)
* django-image-cropping (pip)
* easy-thumbnails (pip)
* django-sortedm2m (pip)
* requests (pip)
* sqlite3 (for development)
* postgres (for production)
* gunicorn (for production)

Optional dependencies
* Virtual Env (for encapsulating the projects dependencies)

## Development
1. Install all dependencies. Pip dependencies can be installed using the requirements.txt file `pip install -r requirements.txt` from the project root, once the repository has been cloned.
2. Create the local database. On development we use sqlite. This can be done using `make migrate` if make is installed. Otherwise one must run `python manage.py makemigrations website && python manage.py migrate`
3. Create a super user using `python manage.py createsuperuser` to manage the admin interface.
4. The scripts `python manage.py importpubs` and `python manage.py importtalks` will import from bibtex and xml files located under the import directory respectively. These files are designed for use by the Makeability lab and will import from Jon Froehlich's website cs.umd.edu/~jonf
5. Add a file googleaccount.py in the website directory. This file should contain only the line ANALYTICS_ACCOUNT = 'your_google_analytics_email'. Replace your_google_analytics_email with whatever google account has been set up to track the domain in google analytics.
6. Follow the instructions [here](https://developers.google.com/analytics/devguides/reporting/core/v3/quickstart/service-py) to install google analytics api using pip, and to download the p12 private key from google analytics for authentication. This file should also go in the website directory along with the googleaccount.py file.
7. Run server using `python manage.py runserver`.

# Troubleshooting
## Bind for 0.0.0.0:8000 failed: port is already allocated
This means that there is already some process running at `0.0.0.0:8000`. First, make to close out of any windows that might be running a local server on your computer. If this error is still occuring, there might be a Docker container that is still running. 

To delete the container, do the following steps:
1. Run `docker ps -a`.
2. A table should be displayed. Look for the row that has `0.0.0.0:8000->8000/tcp` under the ports column. Copy the container name (under the `NAMES` column). 
3. Run `docker kill [NAME]`. (EX: `docker kill confident_tereshkova`). 

## Operational Error: Table/Column does not exist
WARNING: This method resets the database. 
1. Run `make dbshell` to enter an interactive terminal to view the current tables. In the interactive terminal, type `.tables` to display all tables that are listed in the database. (If the problem is that a column doesn't exist, type `.schema [table name]` to display the information about a specific table). If the table/column doesn't exist, continue.
2. Create a second docker container that mounts the database using `docker run -ti -v database:/database ubuntu`
3. Move the database. Type: `cd /database` then `mv db.sqlite3 db.sqlite3.backup`. Exit the interactive terminal.
4. Run `make dbshell`. Find the information for the table that is missing (either entirely or just a column) using `.schema [table name]`. Copy this information.

(You should copy something that might look something like this):
```
CREATE TABLE "website_talk_keywords" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "talk_id" integer NOT NULL REFERENCES "website_talk" ("id"), "keyword_id" integer NOT NULL REFERENCES "website_keyword" ("id"));
CREATE UNIQUE INDEX "website_talk_keywords_talk_id_fbb52519_uniq" ON "website_talk_keywords" ("talk_id", "keyword_id");
CREATE INDEX "website_talk_keywords_393ebc1b" ON "website_talk_keywords" ("talk_id");
CREATE INDEX "website_talk_keywords_5c003bba" ON "website_talk_keywords" ("keyword_id");
```
5. Move the copied database back into place using: `mv db.sqlite3.backup db.sqlite3`.
6. Recreate the database. Run `make shell`. In the interactive terminal, type `python manage.py`.
7. Rerun the website with `make run`.
