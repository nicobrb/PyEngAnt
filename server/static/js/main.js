/*
*
*
*
*/

const fps_enum = {1:1000,2:500,3:330, 4:250, 5:200, 6:166, 7:143, 8:125, 9:111, 10:100} // for setting interval function updates
const playback_rate_enum = {1:1,2:0.5,3:0.333,4:0.25,5:0.2,6:0.166,7:0.142,8:0.125,9:0.111,10:0.1}
const DEFAULT_ENG_VALUE = 'null';
const DEFAULT_IMAGE_URI = "static/images/profile_picture.png"; //default image into the video frame section
const DEFAULT_FPS_RATE = 2;
const DEFAULT_PLAYBACK_RATE = 2; // default playback x2 for a video
const AUs_class = ['AU01_r','AU02_r','AU04_r','AU05_r','AU06_r','AU07_r','AU09_r','AU10_r','AU12_r','AU14_r',
             'AU15_r','AU17_r','AU20_r','AU23_r','AU25_r','AU26_r','AU45_r','AU28_c']; // Header for Action Units

// socket.io params to establish a WebSocket Connection
var socket = io({ path:'/socket.io',
                  reconnection: true,
                  reconnectionAttempts: 3,
                  reconnectionDelay:500,
                  reconnectionDelayMax: 500,
                  randomizationFactor: 0.2,
                  timeout: 12000,
                  autoConnect: true,
                });
var namespace = "/session";
var ping_timeout_counter = 0;

// video object and params
var video = document.querySelector('#videoElement');
video.playbackRate = playback_rate_enum[DEFAULT_PLAYBACK_RATE];
var canvas = document.querySelector('#canvasElement');
var ctx = canvas.getContext('2d');
var w, h, ratio; //video dimensions for adapting frame into img space
let photo = document.getElementById('photo'); // img tag for displaying output frames
var input_check = null; //string that identify the chosen type of input
var stopped = false; // check if a input session is ended

// for ending modal result
var end_eng_value = "null";
var end_eng_label = "";

//webcam input params
var localMediaStream = null;
//video input params
var input_file = document.getElementById('video-file-input'); // for video files selection

var chart = createChart(); // call a function that initialize a Chart
var face_data_table_div = document.getElementById('face_data'); // div that contains the face data table
var timestamp_start = Date.now(); // initialize a timestamp
const log_face_data_table_header = face_data_table_div.innerHTML; // face data table div header (initial content)
var log_last_message = document.getElementById('log_last_message');
var log_message_dd = document.getElementById('log_message_dd');
const default_log_message_dd = log_message_dd.innerHTML;
var session_id = null;
var fps = DEFAULT_FPS_RATE; // starting fps value
var playback = DEFAULT_PLAYBACK_RATE;
var starting_seq_size = 300; // starting seq_size value


// for saving datas switches
var saveCSV = $("#saveCSV").is(":checked")
var saveVIDEO = $("#saveVIDEO").is(":checked")

var framearr = []; // for saving output video file
var eng_data = []; // for saving csv datas
var csv_a = document.getElementById('csv_a');
var webm_a = document.getElementById('webm_a');

//starting situation
document.querySelector('#stop_btn').setAttribute('disabled',true);
document.querySelector('#fps_range').value = fps;
document.querySelector('#streaming_playback_range').value = playback;


function addLogMessage(message){
  
  console.log('log message:'+message);
  document.getElementById('log_last_message').innerHTML = "Log - " + message;
  document.getElementById('log_message_list').innerHTML = document.getElementById('log_message_list').innerHTML + 
                                '<span>' +
                                message +
                                '</span><br>';
}

// alert check for video input compatibility
if (window.File && window.FileReader && window.FileList && window.Blob) {
  // Great success! All the File APIs are supported.
  addLogMessage("INFO: ok. FIle APIs compatible. Video input enabled.")
} else {
  addLogMessage("WARNING: The File APIs are not fully supported in this browser. Video input disabled.")
  document.querySelector('#videoInput').setAttribute('disabled',true);
}
		
// Add a listener to wait for the 'loadedmetadata' state so the video's dimensions can be read
video.addEventListener('loadedmetadata', function() {
  // Calculate the ratio of the video's width to height
  ratio = video.videoWidth / video.videoHeight;
  // Define the required width as 100 pixels smaller than the actual video's width
  w = video.videoWidth - 100;
  // Calculate the height based on the video's width and the ratio
  h = parseInt(w / ratio, 10);
  // Set the canvas width and height to the values just calculated
  canvas.width = w;
  canvas.height = h;			
}, false);

// Takes a snapshot of the video
function snap() {
  // Define the size of the rectangle that will be filled (basically the entire element)
  ctx.fillRect(0, 0, w, h);
  // Grab the image from the video
  ctx.drawImage(video, 0, 0, w, h);
  timestamp_start = Date.now();
}

// webcam input button check (start directly an analysis)
$("#webcamInput").click(function(){
  $("#start_btn").trigger("startAnalysis",'webcam');
  // inserire qui opzioni per input da webcam
});

// video input button check (select the video file before starting an analysis)
$("#videoInput").click(function(){
  input_file.type = 'file';

  input_file.onchange = e => { 
    let video_file = e.target.files[0];
    if(video_file.type != "video/mp4" && video_file.type != "video/webm" && video_file.type != "video/ogg"){
      alert("ERROR: Not valid video file. Choose a correct format of video file. (.mp4/.webm/.ogg)");
    }else{
      var reader = new FileReader();
      reader.onload = (function(theFile) {
        return function(e) {
          video.src = e.target.result;
          $("#start_btn").trigger("startAnalysis",'video');
        }
      })(video_file);
      reader.readAsDataURL(video_file);
      //let fileURL = URL.createObjectURL(video_file);
      //video.src =  fileURL;
    }
  }
  input_file.click();
  //$("#start_btn").trigger("startAnalysis",'video');
  // inserire qui opzioni per input da webcam
});

// Ending analysis listener
document.querySelector('#stop_btn').onclick = function(){
  $("#stop_btn").trigger("stopAnalysis","client_stop");
}
video.onended = function() {
  $("#stop_btn").trigger("stopAnalysis","video_end");
};

// try for adding pagination in face data table
document.getElementById('eng_data_table').onchange = function () {
  $('#eng_data_table').DataTable();
  $('.dataTables_length').addClass('bs-select');
};

/*$(document).ready(function () {
  $('#eng_data_table').DataTable();
  $('.dataTables_length').addClass('bs-select');
});*/

// function that send a video file frame
function sendSnapshot(){
  //ctx.drawImage(video, 0, 0,video.videoWidth, video.videoHeight);
  snap();
  //let image = cv.imread(canvas);
  let dataURL = canvas.toDataURL('image/jpeg');
  let formatted_time =  msToTime(video.currentTime * 1000); // * 1000 for milliseconds

  socket.emit('input_image', {"image":dataURL,"current_time":formatted_time});
}

// function that send a webcam frame
function sendWebcamSnapshot() {
  if (!localMediaStream) {
    return;
  }
  sendSnapshot();
}

// function that establish a WebSocket connection
function Connect(){
  socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port + namespace);
  
  socket.on('connect', function() {
    console.log('Connected!');
    addLogMessage('INFO: Connected.')
  });

  socket.on('check_session_id_response',function(data){
    session_id = data.session_id;
    console.log('session_id:',session_id);
    startStreaming(data.input_type);
  });

  socket.on('output_data',function(data){
    var img = new Image();   
    //img.src = dataURL //data.image_data
    //photo.setAttribute('src', data.image_data);
    photo.style.backgroundImage = "url('"+data.image_data+"')";
    
    // push for video and csv export
    
    if(saveVIDEO == true){
      framearr.push(data.image_data);
    }
    eng_data.push(data.eng_data);

    string = '<tr>';
    Object.keys(data.eng_data).forEach(function(key) {
      if(key === 'timestamp'){
        let date = new Date(data.eng_data[key] * 1000); // multiply *1000 because timestamp is in milliseconds
        //string += '<td>' + date.toLocaleString("it-IT") + '</td>';
        data.eng_data[key] = date.toDateString()+" "+date.getHours()+":"+date.getMinutes()+":"+date.getSeconds();
      }else if(isFloat(data.eng_data[key])){
        //string += '<td>' +  + '</td>';
        data.eng_data[key] = data.eng_data[key].toFixed(2);
      }
      string += '<td>' + data.eng_data[key] + '</td>';
    });
    string += '</tr>';
    face_data_table_div.innerHTML = string + face_data_table_div.innerHTML;
    // adding data to chart
    addData(chart,data.eng_data.frame,data.eng_data.eng_val);
    // updating end_eng_value
    if(parseFloat(data.eng_data.eng_val) != NaN && (parseFloat(data.eng_data.eng_val) != null)){
      end_eng_value = data.eng_data.eng_val;
    }
    // for deleting old chart datas
    if(chart.data.labels.length >= (3 * starting_seq_size)){
      shiftData(chart);
    }
    // updating AU progress bars 
    UpdateAus(data.eng_data);
    console.log('time elapsed:',(Date.now()-timestamp_start)*0.001);
  });

  socket.on("log_message",function(response){
    let message = response;
    addLogMessage(message);
  });

  socket.on("disconnect", (reason) => {
    $('.loading-modal').addClass('d-none');
    if(reason == "io server disconnect"){
      finalize_session();
    }
    else if (reason == "io client disconnect"){
      finalize_session();
      alert("Client disconnesso. Analisi terminata.");
      addLogMessage("INFO: Client disconnected. Analysis endend.")
    }else if (reason == "transport close" || reason == "transport error"){
      socket.connect();
      finalize_session();
      addLogMessage("ERROR: Engant disconnected. Analysis failed.")
    }else if(reason == "ping timeout"){
      ping_timeout_counter++;
      addLogMessage("WARNING: Ping timeout.")
      if(ping_timeout_counter>2){
        socket.connect();
        finalize_session();
        addLogMessage("ERROR: Unstable connection. Analysis failed.")
        ping_timeout_counter = 0;
      }
    }
  });
}

$("#start_btn").on('startAnalysis', function StartAnalysis(event, input_type){
  input_check = input_type;
  stopped = false;
  session_id = null;
  end_eng_value = DEFAULT_ENG_VALUE;
  document.querySelector('#start_btn').setAttribute('disabled',true);
  $('.loading-modal').removeClass('d-none');
  document.querySelector('#stop_btn').removeAttribute('disabled');
  //document.querySelector('#saveCSV').setAttribute('disabled',true);
  document.querySelector('#saveVIDEO').setAttribute('disabled',true);
  document.querySelector('#fps_range').setAttribute('disabled',true);
  document.querySelector('#streaming_playback_range').setAttribute('disabled',true);
  csv_a.style.display = 'none';
  webm_a.style.display = 'none';
  saveCSV = $("#saveCSV").is(":checked");
  saveVIDEO = $("#saveVIDEO").is(":checked");

  fps = document.querySelector('#fps_range').value;
  playback = document.querySelector('#streaming_playback_range').value;
  video.playbackRate = playback_rate_enum[playback];
  
  framearr = [];
  eng_data = [];

  log_message_dd.innerHTML = default_log_message_dd;
  face_data_table_div.innerHTML = log_face_data_table_header;

  Connect();

  let session_params = {'fps':fps,'seq_size':starting_seq_size,'input_type':input_type};
  socket.emit('check_session_id',session_params);
  
});

function startStreaming(input_type){

  $('.loading-modal').addClass('d-none');

  if(input_type == "webcam"){

    navigator.mediaDevices.getUserMedia({audio: false, video: true}).then(function(stream) {
      video.srcObject = stream;
      localMediaStream = stream;
      video.play();
      let send_webcam_frame = setInterval(function () {
        try{
          if(stopped){
            //alert("check if stopped");
            throw new ErrorEvent("Analysis stopped");
          }
          sendWebcamSnapshot();
        }catch (error) {
          console.log(error);
          clearInterval(send_webcam_frame);
          video.pause();
          endTracks();
        }
      }, fps_enum[fps]);
      
    })
    .catch(function(error) {
      console.log(error);
      video.pause();
      endTracks();
    });
  }else if(input_type == "video"){
    video.play();
    let send_video_frame = setInterval(function () {
      try{
        if(stopped){
          //alert("check if stopped");
          throw new ErrorEvent("Analysis stopped");
        }
        sendSnapshot();
      }catch (error) {
        console.log(error);
        clearInterval(send_video_frame);
        video.pause();
      }
    }, fps_enum[fps]);

  }else{
    console.log("ERROR: choose the corret format of video file input.");
  }
}

$("#stop_btn").on('stopAnalysis', function StopAnalysis(event, stop_type){

  stopped = true;
  video.pause();
  endTracks();
  canvas.src = "";

  if(stop_type == "client_stop"){
    addLogMessage("INFO: Ending Analysis.")

    socket.emit('client_disconnect_request');

  }else if(stop_type == "video_end"){
    //alert("Riproduzione video conclusa. Finisco analisi.");
    socket.emit('client_video_end_disconnect_request');
    //socket.emit('client_disconnect_request');

  }else{
    
  }
  /*let disconnected_socket = socket.disconnect();
  console.log("Disconnected Socket:",disconnected_socket);
  sessionStorage.clear();
  localStorage.clear();
  var cookies = document.cookie.split(";");
  for (var i = 0; i < cookies.length; i++)
    eraseCookie(cookies[i].split("=")[0]);
  */
});

function finalize_session(){
  document.querySelector('#start_btn').removeAttribute('disabled');
  document.querySelector('#stop_btn').setAttribute('disabled',true);
  document.querySelector('#saveCSV').removeAttribute('disabled');
  document.querySelector('#saveVIDEO').removeAttribute('disabled');
  document.querySelector('#fps_range').removeAttribute('disabled');
  document.querySelector('#streaming_playback_range').removeAttribute('disabled');
  document.getElementById('video-file-input').removeAttribute('src');
  saveCSV = $("#saveCSV").is(":checked");
  saveVIDEO = $("#saveVIDEO").is(":checked");
  input_file.value = '';
  endTracks();
  // the disconnection was initiated by the server, you need to reconnect manually
  stopped = true;
  video.pause();
  video.src = "";
  video.srcObject = null;
  localMediaStream = null;
  photo.style.backgroundImage = "url('"+DEFAULT_IMAGE_URI+"')";
  flushData(chart);
  let file_name = getDownloadName(session_id, fps, playback);

  if(parseFloat(end_eng_value) < 0.25 ){
    end_eng_label = "Not Engaged";
  } else if (parseFloat(end_eng_value) < 0.50 ){
    end_eng_label = "Slightly Engaged";
  } else if (parseFloat(end_eng_value) < 0.75 ){
    end_eng_label = "Engaged";
  } else if (parseFloat(end_eng_value) < 1.00 ){
    end_eng_label = "Highly Engaged";
  } else{
    end_eng_label = "Not much datas for analysis";
  }
  document.getElementById('end_eng_value').innerHTML = end_eng_value;
  document.getElementById('end_eng_label').innerHTML = end_eng_label;
  $('#endModal').modal('show');

  if(saveCSV == true && eng_data.length > 0){
    addLogMessage("INFO: Creating the CSV file that contains face datas")
    let csv_link = getLinkCSV(eng_data, file_name);
    csv_a.setAttribute("download", file_name+".csv");
    csv_a.setAttribute("href", csv_link);
    csv_a.style.display = '';
  }
  if(saveVIDEO == true && framearr.length > 0){
    addLogMessage("INFO: Creating the video of the analysis session")
    let webm_link = getLinkVideo(framearr, 15, file_name);
    webm_a.setAttribute("download", file_name+".webm");
    webm_a.setAttribute("href", webm_link);
    webm_a.style.display = '';
  }
  addLogMessage("INFO: Analysis ended.")
}

function UpdateAus(data){
  AUs_class.forEach(function(au_class){
    if(au_class == "AU28_c"){
      valeur = (data[au_class]* 100);
      //document.querySelector('#'+au_class).setAttribute('aria-valuenow',data[au_class]);
      $('#'+au_class).css('width', valeur+'%').attr('aria-valuenow', data[au_class]);
    }else{
      valeur = (data[au_class]* 100) / 5;
      //document.querySelector('#'+au_class).setAttribute('aria-valuenow',data[au_class]);
      $('#'+au_class).css('width', valeur+'%').attr('aria-valuenow', data[au_class]);   
    } 
  });
}

function endTracks(){
  if(input_check == "webcam"){
    try{
      localMediaStream.getTracks().forEach(function(track) {
        track.stop();
      });
    }catch (error) {
      console.log(error);
    }
  }
}


