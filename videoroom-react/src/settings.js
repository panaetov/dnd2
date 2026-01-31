// Settings from settings.js - same parameters
let server = null;
if(window.location.protocol === 'http:')
	server = "http://" + window.location.hostname + ":8088/janus";
else
	server = "https://" + window.location.hostname + ":8089/janus";

server = "http://51.250.102.96:8088/janus";

var iceServers = [
    {urls: "stun:stun.l.google.com:19302"},
    {urls: "turn:free.expressturn.com:3478", username: "000000002084126365", credential: "4kbbi1XtfrmjnuxOkgfmU1gF6zw="},
    {urls: "turn:relay1.expressturn.com:80", username: "000000002084126365", credential: "4kbbi1XtfrmjnuxOkgfmU1gF6zw="},
    {urls: "turn:relay1.expressturn.com:443", username: "000000002084126365", credential: "4kbbi1XtfrmjnuxOkgfmU1gF6zw="},
    {urls: "turn:relay1.expressturn.com:3478", username: "000000002084126365", credential: "4kbbi1XtfrmjnuxOkgfmU1gF6zw="},
    {urls: "turn:relay2.expressturn.com:3478", username: "000000002084126365", credential: "4kbbi1XtfrmjnuxOkgfmU1gF6zw="},
    {urls: "turn:relay3.expressturn.com:3478", username: "000000002084126365", credential: "4kbbi1XtfrmjnuxOkgfmU1gF6zw="},
    {urls: "turn:relay4.expressturn.com:3478", username: "000000002084126365", credential: "4kbbi1XtfrmjnuxOkgfmU1gF6zw="},
    {urls: "turn:relay5.expressturn.com:3478", username: "000000002084126365", credential: "4kbbi1XtfrmjnuxOkgfmU1gF6zw="},
    {urls: "turn:relay6.expressturn.com:3478", username: "000000002084126365", credential: "4kbbi1XtfrmjnuxOkgfmU1gF6zw="},
    {urls: "turn:relay7.expressturn.com:3478", username: "000000002084126365", credential: "4kbbi1XtfrmjnuxOkgfmU1gF6zw="},
    {urls: "turn:relay8.expressturn.com:3478", username: "000000002084126365", credential: "4kbbi1XtfrmjnuxOkgfmU1gF6zw="},
    {urls: "turn:relay9.expressturn.com:3478", username: "000000002084126365", credential: "4kbbi1XtfrmjnuxOkgfmU1gF6zw="},
    {urls: "turn:relay10.expressturn.com:3478", username: "000000002084126365", credential: "4kbbi1XtfrmjnuxOkgfmU1gF6zw="},
    {urls: "turn:relay11.expressturn.com:3478", username: "000000002084126365", credential: "4kbbi1XtfrmjnuxOkgfmU1gF6zw="},
    {urls: "turn:relay12.expressturn.com:3478", username: "000000002084126365", credential: "4kbbi1XtfrmjnuxOkgfmU1gF6zw="},
    {urls: "turn:relay13.expressturn.com:3478", username: "000000002084126365", credential: "4kbbi1XtfrmjnuxOkgfmU1gF6zw="},
    {urls: "turn:relay14.expressturn.com:3478", username: "000000002084126365", credential: "4kbbi1XtfrmjnuxOkgfmU1gF6zw="},
    {urls: "turn:relay15.expressturn.com:3478", username: "000000002084126365", credential: "4kbbi1XtfrmjnuxOkgfmU1gF6zw="},
    {urls: "turn:relay16.expressturn.com:3478", username: "000000002084126365", credential: "4kbbi1XtfrmjnuxOkgfmU1gF6zw="},
    {urls: "turn:relay17.expressturn.com:3478", username: "000000002084126365", credential: "4kbbi1XtfrmjnuxOkgfmU1gF6zw="},
    {urls: "turn:relay18.expressturn.com:3478", username: "000000002084126365", credential: "4kbbi1XtfrmjnuxOkgfmU1gF6zw="},
    {urls: "turn:relay19.expressturn.com:3478", username: "000000002084126365", credential: "4kbbi1XtfrmjnuxOkgfmU1gF6zw="},
    {urls: "turn:global.expressturn.com:3478", username: "000000002084126365", credential: "4kbbi1XtfrmjnuxOkgfmU1gF6zw="}
];
var iceTransportPolicy = 'all';

export { server, iceServers, iceTransportPolicy };
