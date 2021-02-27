
// TODO
// 2
// сделать article relative
// и считать общую позицию ссылки, складывая позицию карточки и ссылки внутри карточки

// 3
// ДВОЙНЫЕ СТРОКИ?
// считать не высоте строки а на текущей позиции первой строки ренджа

// 4
// что если карточек много и прокрутка левой части?

// 5
// прокрутка кода с границами

// init:
const topSourceScrollLimit = 200;
let bottomSourceScrollLimit; // TODO update on window resize
let mainContainer;
let referContainer;
let sourceContainer;
let sourceContainerHeight;
let sourceBlock;
let sourceBlockHeight; // TODO update on window resize
let translateSourceBlockTo;
let stringHeight = 24;
let highlightBlock;
let requirements = [];
let requirementsPositions = {};
let pointers = [];
let pointersPositions = {};

window.onload = function () {

  // get Containers
  mainContainer = document.getElementById('mainContainer');
  referContainer = document.getElementById('referContainer');
  sourceContainer = document.getElementById('sourceContainer');

  // add MouseWheelHandler
  sourceContainer.addEventListener("wheel", MouseWheelHandler);
  sourceContainerHeight = sourceContainer.offsetHeight;

  // get sourceBlock
  sourceBlock = document.getElementById('source');
  sourceBlockHeight = sourceBlock.offsetHeight;

  bottomSourceScrollLimit = sourceContainerHeight - sourceBlockHeight - topSourceScrollLimit;

  // get highlightBlock
  highlightBlock = sourceBlock.querySelector('.source_highlight');

  // get requirements NodeList; convert it to array:
  requirements = [...document.querySelectorAll('.requirement')];
  // get pointers NodeList; convert it to array:
  pointers = [...document.querySelectorAll('.pointer')];

  requirements.map((element) => {
    // ID format of DOM element is 'requirement:ID'
    const id = element.id.split(':')[1];
    // set requirementsPositions
    requirementsPositions = {
      ...requirementsPositions,
      [id]: element.offsetTop
    };
  })

  pointers.map((element) => {
    // set pointersPositions
    pointersPositions = {
      ...pointersPositions,
      [element.id]: element.offsetTop
    };
    // add addEventListener on click
    element.addEventListener("click",
      function () {
        toggleRequirement(this.id);
      }
    );
  })

  // TODO relative pos = REQ pos - LINE pos
  stringHeight = document.getElementById('line-2').offsetTop;

  // fire on load:
  toggleRequirement();

  console.log('pointers: ', pointers);
  console.log('requirementsPositions: ', requirementsPositions);
  console.log('pointersPositions: ', pointersPositions);

};

function toggleRequirement(pointerID) {

  // prepare params
  if (!pointerID) {
    // get params from URL:
    pointerID = window.location.hash.substring(1);
  }
  [reqId, rangeStart, rangeEnd] = pointerID.split(':');

  // toggle active requirement
  requirements.map((element) => {
    element.classList.remove('active');
    // ID format of DOM element is 'requirement:ID'
    if (element.id === `requirement:${reqId}`) {
      element.classList.add('active');
    }
  })

  // toggle active pointer
  pointers.map((element) => {
    element.classList.remove('active');
    if (element.id === pointerID) {
      element.classList.add('active');
    }
  })

  // prepare variables for translate
  const rangeSize = (rangeEnd - rangeStart + 1) || 0;
  const rangeAmend = (rangeStart - 1) * stringHeight || 0;

  translateSourceBlockTo = pointersPositions[pointerID] - rangeAmend;

  // translate
  sourceBlock.style.transform = 'translateY(' + translateSourceBlockTo + 'px)';
  highlightBlock.style.top = rangeAmend + 'px';
  highlightBlock.style.height = rangeSize * stringHeight + 'px';
  // reset sourceContainer scroll limit indicator
  sourceContainer.classList.remove('limit-top');
  sourceContainer.classList.remove('limit-bottom');

  console.log('translateSourceBlockTo: ', translateSourceBlockTo);
}

function MouseWheelHandler(e) {
  // reset sourceContainer scroll limit indicator
  sourceContainer.classList.remove('limit-top');
  sourceContainer.classList.remove('limit-bottom');

  const delta = e.deltaY;

  const isScrollBottom = delta < 0;
  // console.log('delta: ', delta);

  const style = window.getComputedStyle(sourceBlock);
  const matrix = new WebKitCSSMatrix(style.transform);
  const currTranslate = Math.round(matrix.m42);
  let nextTranslate = Math.round(currTranslate - delta);

  if (isScrollBottom && currTranslate > topSourceScrollLimit) {
    nextTranslate = currTranslate;
    sourceContainer.classList.add('limit-top');
  }

  if (!isScrollBottom && currTranslate < bottomSourceScrollLimit) {
    nextTranslate = currTranslate;;
    sourceContainer.classList.add('limit-bottom');
  }

  sourceBlock.style.transform = 'translateY(' + nextTranslate + 'px)';
  return false;
}
