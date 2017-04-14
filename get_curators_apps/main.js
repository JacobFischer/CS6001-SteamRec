const http = require('http');

let $ = null;
require("jsdom").env("", function(err, window) {
    if (err) {
        console.error(err);
        return;
    }

    $ = require("jquery")(window);

    const HOST = 'store.steampowered.com';
    const PATH = '/curators/ajaxgetcuratorrecommendations/1370293/';

    var options = {
      host: HOST,
      path: PATH + '?start=117&count=50',
    };

    var regex = new RegExp('(appid=\\")(.*?)\"');

    function callback(response) {
      let str = '';

      //another chunk of data has been received, so append it to `str`
      response.on('data', function(chunk) {
        str += chunk;
      });

      //the whole response has been received, so we just print it out here
      response.on('end', function() {
        //const groups = regex.exec(str);
        const parsed = JSON.parse(str)
        const html = $(parsed.results_html);
        const found = html.find("div[data-ds-appid]");
        let ids = [];

        for(let i = 0; i < found.length; i++) {
            ids.push($(found[i]).attr('data-ds-appid'))
        }

        console.log(ids);
      });
    }

    http.request(options, callback).end();
});

// TODO: use as function for variable curator id, start, and count
