"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
var getRandoms = exports.getRandoms = function getRandoms(length, threshold) {
  var tooClose = function tooClose(a, b) {
    return Math.abs(a - b) < threshold;
  };

  var result = [];
  var random = void 0;

  for (var i = 0; i < length; i += 1) {
    random = Math.random();
    if (i !== 0) {
      var prev = result[i - 1];
      while (tooClose(random, prev)) {
        random = Math.random();
      }
    }
    result.push(random);
  }
  return result;
};

var randomToDelay = exports.randomToDelay = function randomToDelay(random, min, max) {
  var float = random * (max - min);
  return parseInt(float, 10) + min;
};