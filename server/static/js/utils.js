//util functions

function isFloat(n) {
  return n === +n && n !== (n|0);
}

function msToTime(s) {
  var ms = s % 1000;
  s = (s - ms) / 1000;
  var secs = s % 60;
  s = (s - secs) / 60;
  var mins = s % 60;
  var hrs = (s - mins) / 60;

  return hrs + ':' + mins + ':' + secs + '.' + Math.floor(ms);
}


function ConvertToCSV(objArray) {
    let rows = typeof objArray !== "object" ? JSON.parse(objArray) : objArray;
    let header = "";
    Object.keys(rows[0]).map(pr => (header += pr + ";"));

    let str = "";
    rows.forEach(row => {
      let line = "";
      let columns =
        typeof row !== "object" ? JSON.parse(row) : Object.values(row);

      columns.forEach(column => {
        if (line !== "") {
          line += ";";
        }
        if (typeof column === "object") {
          line += JSON.stringify(column);
        } else {
          line += column;
        }
      });
      str += line + "\r\n";
    });
    return header + "\r\n" + str;
}

function getLinkCSV (data, filename) {
  var result = ConvertToCSV(data);
  let fileToSave = new Blob([result], {
     type: "csv",
     name: filename+".csv"
  });
  /*saveAs(fileToSave, filename);*/
  var url = webkitURL.createObjectURL(fileToSave);
  return url;
}

function createVideo (frame_list, fps) {
  whammy_video = Whammy.fromImageArray(frame_list, fps);
  return whammy_video;
}

function getLinkVideo(frame_list, fps, filename){
  var result = createVideo(frame_list,fps);
  let fileToSave = new Blob([result], {
    type: "webm",
    name: filename+".webm"
  });
  var url = webkitURL.createObjectURL(fileToSave);
  return url;
}

function getDownloadName(session_id,fps,playback){
  let date = new Date(Date.now());
  let filename = date.toDateString()+"_"+date.getHours()+"_"+date.getMinutes()+"_"+date.getSeconds()+'_session_'+session_id+'_fps_'+fps+'_pb_'+playback;
  return filename;
}