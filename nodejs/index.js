require("dotenv").config();

const express = require("express");
const cors = require("cors");

const { QUERIES, PHRASES } = require("./queries");

const port = process.env.PORT || 8080;
const app = express();

const corsOptions = {
  origin: [process.env.CORS_ORIGIN_DEV, process.env.CORS_ORIGIN_PROD],
  optionsSuccessStatus: 200,
};

app.use(cors(corsOptions));

const LANG = "es";
const QUERY_STRING = QUERIES[LANG].map(s => `(${s})`).join(" OR ");
const mQueue = PHRASES[LANG];

const QUEUE_SIZE = 64;
let insertIndex = 0;
let popIndex = 0;

//   stream.on('data', (tweet) => {
//     let mText = tweet.text.replace(/RT /g, '');
//     mText = mText.replace(/["{}<>().!,;|\-]/g, '');
//     mText = mText.replace(/[#@]\S+/g, '');
//     mText = mText.replace(/http(s?):\/\/\S+/g, '');
//     mText = mText.replace(/b\/c/g, 'because');
//     mText = mText.replace(/([a-zA-Z]+)\/([a-zA-Z]+)/g, '$1 $2');
//     mText = mText.replace(/\S+…/g, '');
//     mText = mText.replace(/\s+/g, ' ');
//     mText = mText.trim();

//     if(mText.length > 0) {
//       console.log(mText);
//       if(mQueue.length < QUEUE_SIZE) {
//         mQueue.push(mText);
//       } else {
//         mQueue[insertIndex] = mText;
//         insertIndex = (insertIndex + 1) % mQueue.length;
//       }
//     }
//   });

app.get("/AFT", (_, res) => {
  res.send(mQueue[popIndex]);
  popIndex = (popIndex + 1) % mQueue.length;
});

app.get("/AFTALL", (_, res) => {
  res.send(mQueue.join("<br>"));
});

app.listen(port);
