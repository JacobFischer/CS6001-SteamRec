const fs = require('fs');
const request = require('request');

const URL = 'http://store.steampowered.com/curators/ajaxgetcuratorrecommendations/';
const COUNT_BY = 50;
const FILES_DIR = './curators_apps/';

var text = fs.readFileSync(process.argv[2] || "./curators.txt").toString();
var textByLine = text.split("\n");
const jquery = {}; // way to pass jquery around after it's loaded

// main entry point, tries to asynchronously generate a file
function generateFile(index, callback) {
  let curatorID = textByLine[index];
  if(!curatorID) {
    return callback(); // we are done!
  }

  curatorID = curatorID.trim();

  const filepath = `${FILES_DIR}${curatorID}.json`;
  fs.access(filepath, fs.constants.R_OK, (err) => {
    if(!err || err.code !== 'ENOENT') {
      // skip, file exists or some other found
      console.log(`${index}: Skipping ${curatorID}`);
      generateFile(index + 1, callback)
    }
    else { // err.code === 'ENOENT'
      getCuratorsApps(curatorID, function(ids) {
        console.log(`${index}: Generated file for ${curatorID}`);
        fs.writeFile(filepath, JSON.stringify(ids), 'utf8', function() {
          generateFile(index + 1, callback);
        });
      });
    }
  });
}


function getSomeIDs(curatorID, index, callback) {
  request(`${URL}${curatorID}/?start=${index}&count=${COUNT_BY}`, function(error, response, body) {
      const parsed = JSON.parse(body)
      const html = jquery.$(parsed.results_html);
      const found = html.find("div[data-ds-appid]");
      let ids = [];

      for(let i = 0; i < found.length; i++) {
          ids.push(jquery.$(found[i]).attr('data-ds-appid'))
      }

      callback(ids);
  });
}

function getAllIDs(curatorID, i, list, callback) {
  getSomeIDs(curatorID, i * COUNT_BY, function(ids) {
    if (ids.length === 0) {
      // found no ids, so we are done
      callback(list);
    }
    else {
      // we found some ids, add them then do this again
      list.push.apply(list, ids);
      getAllIDs(curatorID, i + 1, list, callback);
    }
  })
}

function getCuratorsApps(curatorID, callback) {
  getAllIDs(curatorID, 0, [], callback);
};

// now actually do the thing
require("jsdom").env("", function(err, window) {
    if (err) {
        console.error(err);
        return;
    }

    // stupid, but we are using jquery in a stupid fashion anyways to parse html server side
    jquery.$ = require('jquery')(window);

    generateFile(0, function() {
      console.log('DONE!');
    })
});

// TODO: use as function for variable curator id, start, and count
