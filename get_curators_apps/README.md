# Get Curators Apps Script

This is a simple package of scripts to scrape the steam website via hijacking their AJAX API so we can record Steam Curator data. Because in Steam's infinite wisdom their official API does not expose this information -__-

## Requirements

This is a Node.js script. You will need Node.js >=6.9.0 installed:

## Scraping the Curators

```
npm install
node main.js
```

This will then read in `curators.txt` and for each entry generate a json file of that name in `./curators_apps/`

## Combining those files

Dealing with 1000 files is a pain, let's combine them into one file.

You can do this via running the script:

```
node filesToOneFile.js
```

This will combine all those generated files into a simple json dictionary, where each key is the curator id, and each value is the contents of that file.

Each curator's file/entry looks like this:

```json
{
  "name": "Name of the Curator",
  "list": [
    {
      "appid": "289130",
      "recommended": true,
      "info": false
    },
    {
      "appid": "221380",
      "recommended": false,
      "info": false
    },
    {
      "appid": "202200",
      "recommended": false,
      "info": true
    }
  ]
}
```

Note that no app in the curator's `list` can be both `recommended` and `info` at the same time. At the time of this writing an app entry in the curator must be one of Recommended, Not Recommended, or Info. An info entry probably doesn't mean much as we don't record the info, but if you want it you can easily edit the script to scrap that as well.

## Questions?

just ask Jacob Fischer:

jacob.t.fischer@gmail.com
