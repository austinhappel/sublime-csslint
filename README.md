# CSSLint plugin for Sublime Text 2

Takes the power of [csslint.net](http://csslint.net) and puts it into Sublime Text. Instead of copying and pasting your CSS into the [csslint.net](http://csslint.net) static analysis tool, all you have to do is hit `ctrl + alt + c` and any warnings are displayed in your console. You can also click on those warnings in the console, and the specific line will be highlighted in your code.

You can also lint multiple files at a time by selecting them in the sidebar and selecing `CSSLint Selection`. A new document will open and display the lint data, sorted by filename.

## Installation

1. Copy this project folder to your Sublime Text Packages folder:

	> Windows:  %APPDATA%\Sublime Text 2\Packages
	
    > Mac OS X: ~/Library/Application\ Support/Sublime\ Text\ 2/Packages/
    
    > Linux:    ~/.config/sublime-text-2/Packages

2. Make sure Java is installed, and that `java` is in your PATH.

3. Rename the package folder from "sublime-csslint" to "CSSLint".

## Usage

* Use the Command Pallete (Windows and Linux: Ctrl+Shift+P, OSX: Command+Shift+P) and search for: 

	> CSSLint: Run CSSLint

* Use a keyboard shortcut. By default this is `ctrl + alt + c`. Change this by adding something like the following to your key bindings:

		{ "keys": ["ctrl+alt+c"], "command": "csslint" }

### Advanced Usage

* Each CSS Lint rule has an ID that can be found in [this file](https://github.com/austinhappel/sublime-csslint/blob/master/scripts/csslint/csslint-rhino.js). (Look for blocks starting with `CSSLint.addRule`).
* To ignore certain rules of CSS Lint, you will need to amend the Preferences > Package Settings > CSS Lint > User Preferences file. This will be blank by default. Just copy/paste the Default preferences file and then amend to suit.
* Therefore as an example:

````
{
    // CSSLint rules you wish to ignore. Must be an array. Leave blank to include all default rules.
    "ignore": ["floats","universal-selector","box-model","unqualified-attributes"]
}
````

This would ignore messages about **floats**, the **universal selector**, **box-model** and **unqualified attributes**.

## Thanks

Much of this plugin has been copied from the [sublime-jslint](https://github.com/fbzhong/sublime-jslint) project. I liked how that plugin worked, and based this project off of it. Much thanks to [fbzhong](https://github.com/fbzhong) for that!

## Other Notes

This plugin uses the [Rhino](http://www.mozilla.org/rhino/download.html) command-line version of CSSLint, and includes the Rhino library.
