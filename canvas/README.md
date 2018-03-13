# To Get This Running...

Get [NW.js](https://nwjs.io) by clicking one of the blue buttons at the top.
I use the **SDK**.

## To start app with appropriate flags:
CD to your NW.js app and run:

`~/nwjs-sdk-v0.27.4-linux-x64/nw --enable-transparent-visuals --disable-gpu --disable-gpu-compositing --force-cpu-draw .`

Where `~/The/path/to/your/NW.js/nw file` is followed by a bunch of `--flags` and a `.`

##To test with aws instance
YOU MUST copy valor-dev.pem into the directory of nwjs-canvas as `key,pem`


## From main window console:

`window.open('chrome://inspect/#apps')`

This lets you inspect nested windows and `<webview>` tags.
