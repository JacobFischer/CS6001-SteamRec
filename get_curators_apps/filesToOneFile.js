var fs = require('fs');
// path to directory with files, where the filename is the curator id, and the contents is the json'd array of appids
const PATH = './curators_apps/';

// read in all the files and store them to make the file contents
const filenames = fs.readdirSync(PATH);
let contents = [];
for (const filename of filenames) {
  const content = fs.readFileSync(PATH + filename).toString();
  const id = filename.replace('.json', '').trim();

  contents.push(`"${id}": ${content}`);
}

// write the single file
const file = `{\n  ${contents.join(',\n  ')}\n}`;
fs.writeFile('./curator_to_appids.json', file, 'utf8', function() {
  console.log('DONE!');
});
