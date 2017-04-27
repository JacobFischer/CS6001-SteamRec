const fs = require('fs');
const request = require('request');
const moment = require('moment');

const URL = 'http://store.steampowered.com/curators/ajaxgetcuratorrecommendations/';
const COUNT_BY = 50;
const FILES_DIR = './curators_apps/';
const CURRENT_YEAR = (new Date()).getFullYear();

let text = fs.readFileSync(process.argv[2] || './curators.txt').toString();
let textByLine = text.split('\n');
const jquery = {}; // way to pass jquery around after it's loaded
let badCurators = [];

function pad(str) {
  return (str.length === 1 ? '0' : '') + str;
}

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
      if(err) {
        console.log(`${curatorID} had some problem accessing file`);
        badCurators.push(curatorID);
      }
      // skip, file exists or some other found
      console.log(`${index}: Skipping ${curatorID}`);
      generateFile(index + 1, callback)
    }
    else { // err.code === 'ENOENT'
      console.log(`${index}: Generating file for ${curatorID}`);
      getCuratorsApps(curatorID, function(name, list) {
        console.log(`  -> Writing file for ${name}`);
        fs.writeFile(filepath, JSON.stringify({name, list}), 'utf8', function() {
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
    const found = html.find('div[data-ds-appid]');
    let ids = [];

    for(let i = 0; i < found.length; i++) {
      const $found = jquery.$(found[i]);

      // try to find the temporal data
      const rawDate = $found.find('.recommendation_type_ctn > span').clone().children().remove().end().text();
      let split = rawDate.trim().replace(',', '').split(' ');
      let day = pad(split[1]);
      let month = moment().month(split[0]).format('MM');
      let year = split[2]; // might not exist

      if(split.length === 2) { // if it doesn't, that means this year
        year = CURRENT_YEAR
      }

      let rfc2822 = `${year}-${month}-${day}`;

      ids.push({
        appid: $found.attr('data-ds-appid'),
        recommended: $found.find('.color_recommended').length > 0, // if this span is found, they recommended it
        info: $found.find('.color_informational').length > 0, // if this span is found, it's an info post
        rawDate: rawDate,
        epoch: Number(moment(rfc2822)),
      });
    }

    callback(ids);
  });
}

function getAllIDs(curatorID, i, list, callback) {
  getSomeIDs(curatorID, i * COUNT_BY, function(ids) {
    if (ids.length === 0) {
      // found no ids, so we are done, now get the name
      getCuratorsName(curatorID, (name) => callback(name, list));
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
}

function getCuratorsName(curatorID, callback) {
  request(`http://store.steampowered.com/curator/${curatorID}/`, (error, response, body) => {
    const html = jquery.$(body);
    callback(html.find('h2.curator_name a').html());
  });
}

// now actually do the thing
require('jsdom').env('', function(err, window) {
    if (err) {
        console.error(err);
        return;
    }

    // stupid, but we are using jquery in a stupid fashion anyways to parse html server side
    jquery.$ = require('jquery')(window);

    generateFile(0, function() {
      console.log('DONE!');
      if (badCurators.length > 0) {
        console.log('Bad Curators:');
        for (const curatorID of badCurators) {
          console.log(curatorID);
        }
      }
    })
});
