
# Gleam-giveaway-bot
Python bot to automatically find and complete gleam giveaways.  

![Demo](https://imgur.com/GE8wlBg.gif)  

## Warning

Usage of this script is forbidden by the TOS of gleam and will probably get you banned.  
**DO NOT USE WITH YOUR REAL ACCOUNTS OR EMAIL.** They will get spammed with messages and potentially flagged for suspicous activity.  
Use at your own risk.

## Prerequisites

- Python3 ([Download](https://www.python.org/downloads/))
 - Chrome WebDriver for your version of Google Chrome ([Download](https://chromedriver.chromium.org/downloads))
 - Include the WebDriver location in your PATH environment variable ([Tutorial](https://zwbetz.com/download-chromedriver-binary-and-add-to-your-path-for-automated-functional-testing/))

## Authentication and setup

- Rename the  [config.json.example](config.json.example) file to "config.json"  
- Install the dependencies: `pip install -r requirements.txt`

- It is strongly recommended that you create a second Chrome Profile. This will isolate your usual social media accounts and 			email from the bot.
To do this:  

	 1. Open Chrome and click on Profile in the top right.
	 2. Click Add
	 3. Choose a name and picture
	 4. With the new profile visit: *chrome://version/*
	 5. Copy the Profile Path (On Windows, should be something like "C:\Users\User\AppData\Local\Google\Chrome\User 		Data\Profile 2" ). 
	 6. Modify the config.json file.   In the "user-data-dir" field enter the path from before up to the "User Data" part with escaped backslashes or forward shlashes (e.g 	"C:/Users/User/AppData/Local/Google/Chrome/User Data"). In the "profile-directory" enter the profile part of the path (e.g "Profile 2").

 - If you want to get giveaways from reddit, [register](https://www.reddit.com/prefs/apps/) an application. Then fill out the reddit_auth section of the config file.
 
 - If you want to complete twitter actions on gleam you have to register for api access [here](https://developer.twitter.com/en/apps). After approval you can fill out the corresponding fields in the config. Again, **do not use your normal twitter account**.
  
## Running the script
After the setup above is completed, close all Chrome windows and start the script (`python giveaway_bot.py`). Now the bot will fetch urls from "http://gleamlist.com" and, if you configured it, from "https://www.reddit.com/r/giveaways/".  

**On first start:**
A browser window should open. Here you have to login with your various accounts. For this, first click on any visit action like the one below. Next, finish the action and fill in the required details. 

![Register](https://imgur.com/4tsJj6U.png)  

Then click on the "Enter with x" elements and connect the corresponding account. The more social media accounts you use, the more entries will be able to be completed.  

When you are done connecting your accounts press any button and the program will resume.
