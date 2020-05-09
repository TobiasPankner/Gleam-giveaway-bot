
# Gleam-giveaway-bot
Python bot to automatically find and complete gleam giveaways.

## Warning

Usage of this script is forbidden by the TOS of gleam and will probably get you banned.  
**DO NOT USE WITH YOUR REAL ACCOUNTS.** They will get spammed with messages and potentially flagged for suspicous activity.

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
	 2. Choose a name and picture
	 3. With the new profile visit: *chrome://version/*
	 4. Copy the Profile Path (On Windows, should be something like "C:\Users\User\AppData\Local\Google\Chrome\User 		Data\Profile 2" ). 
	 5. Modify the config.json file.   In the "user-data-dir" field enter the path from before up to the "User Data" part (e.g 	"C:\Users\User\AppData\Local\Google\Chrome\User Data"). In the "profile-directory" enter the profile part of the path (e.g "Profile 2").

 - If you want to get giveaways from reddit, [register](https://www.reddit.com/prefs/apps/) an application. Then fill out the reddit_auth section of the config file.
 
 - If you want to complete twitter actions on gleam you have to register for api access [here](https://developer.twitter.com/en/apps). After approval you can fill out the corresponding fields in the config. Again, **do not use your normal twitter account**.

- Login with social media accounts on the Chrome profile you are using. Visit the [gleam example page](https://gleam.io/examples/competitions/every-entry-type) and click on any visit action. Finish the action and enter your name and email.
![Register](https://imgur.com/4tsJj6U.png)  

  Then click on the "Enter with x" elements and connect the corresponding account. The more social media accounts you use, the more entries will be able to completed. This can also be skipped.
  
 - Start the script: `python giveaway_bot.py`


