"use strict";

// Variables
//======================================
const hexRadius = 25; // from center to one of the points
const hexLineWeight = 1; // thickness of drawing line
const hexDoubleLineOffset = 6; // space between double lines
const hexMargin = 2; // space around hexagons
const drawLines = true; // draw all the lines
const drawPoints = false; // also draw lone double active hexagons as circles
const zenoSway = 0.2; // hexagon background colour transition scalar
let drawHex = true; // draw hexagon background
let drawGrid = true; // when false the background is the same colour as inactive hexagons
let creatorCount = 1; // start with 1 creator
let destroyerCount = 3; // and 3 destroyers
let drawAgents = true; // colour in agent hexagons red/white
let agentsMoving = true; // animating the agents, toggled with spacebar
let drawMouse = false; // colour in mouse target hexagon in white
let mouseTargetHex; // updated with grid position of hovered mouse
let mouseLastHex; // used for drag drawing
let hexHeight, hexWidth, columns, rows, mousePos;
let hexagons = [];
let agents = [];
// Helper Functions
//======================================
function drawHexagon(pixelPos) {
  // draws hexagon with the center pixelPos
  push();
  translate(pixelPos.x, pixelPos.y);
  beginShape();
  for (let i = 0; i < 6; i++) {
    vertex(
      (hexRadius - hexMargin / 2) * cos((i * Math.PI) / 3),
      (hexRadius - hexMargin / 2) * sin((i * Math.PI) / 3)
    );
  }
  endShape(CLOSE);
  pop();
}
function getEdgePos(i, offset) {
  // return position of this edge of the hexagon
  // if (offset == 1) clockwise from middle edge
  // if (offset == 0) middle of edge
  // if (offset == -1) anti-clockwise from middle edge
  var pos = createVector(offset * hexDoubleLineOffset * 0.5, -hexHeight / 2);
  pos.rotate((i * Math.PI) / 3);
  return pos;
}
function wrap6(num) {
  // -1 => 5
  // 0 => 0
  // 5 => 5
  // 6 => 0
  // 7 => 1
  return (num + 6) % 6;
}
function mouseOnScreen() {
  // return boolean based on whether the mouse is inside the screen or not
  if (mouseX < 0 || mouseX >= width || mouseX === undefined) return false;
  if (mouseY < 0 || mouseY >= height || mouseY === undefined) return false;
  return true;
}
// Setup
//======================================
function setup() {
  // calculate width and height of hexagons
  hexWidth = hexRadius * 2;
  hexHeight = Math.sqrt(3) * hexRadius;
  // set rows and columns to overlap page edge
  columns = Math.ceil(window.innerWidth / (hexRadius * 3));
  rows = Math.ceil(window.innerHeight / (hexHeight / 2)) + 1;
  mousePos = createVector(0, 0);
  // set up canvas
  createCanvas(
    (columns + 1 / 4) * (hexRadius * 3),
    (rows + 1) * (hexHeight / 2)
  );
  frameRate(24);
  // initialise 2D array of hexagons
  for (let x = 0; x < columns; x++) {
    hexagons.push([]);
    for (let y = 0; y < rows; y++) {
      hexagons[x].push(new Hex(x, y));
    }
  }
  // neighbouring needs to be done after they're all initialised
  for (let x = 0; x < columns; x++) {
    for (let y = 0; y < rows; y++) {
      hexagons[x][y].initialiseNeighbours(x, y);
    }
  }
  // initialise agents
  for (let i = 0; i < creatorCount + destroyerCount; i++) {
    let creator = i < creatorCount ? true : false;
    agents.push(new Agent(creator));
  }
}
// Global Draw
//======================================
function draw() {
  if (drawGrid) {
    background(25);
  } else {
    background(9);
  }
  // important to draw all hexagons before lines to avoid overlap
  if (drawHex || drawGrid) {
    for (let y = 0; y < rows; y++) {
      for (let x = 0; x < columns; x++) {
        hexagons[x][y].drawHex();
      }
    }
  }
  if (drawAgents) {
    for (let i = 0; i < creatorCount + destroyerCount; i++) {
      agents[i].draw();
    }
  }
  // draw hexagon at mouse position
  if (drawMouse) drawMouseHexagon();
  if (drawLines) {
    for (let y = 0; y < rows; y++) {
      for (let x = 0; x < columns; x++) {
        hexagons[x][y].drawLines();
      }
    }
  }
  update();
}
// Global Update
//======================================
function update() {
  mousePos.x = mouseX;
  mousePos.y = mouseY;
  if (agentsMoving) {
    for (let i = 0; i < creatorCount + destroyerCount; i++) {
      agents[i].update();
    }
  }
  for (let y = 0; y < rows; y++) {
    for (let x = 0; x < columns; x++) {
      hexagons[x][y].update();
    }
  }
}
// Agent Class
//======================================
class Agent {
  constructor(creator) {
    // randomly place near centre of screen
    this.x = Math.round(columns * (0.3 + random(0.4)));
    this.y = Math.round(rows * (0.3 + random(0.4)));
    // set random direction 0-5
    this.dir = Math.floor(random(0, 6));
    // set its morality
    this.creator = creator;
  }
  draw() {
    noStroke();
    if (this.creator) {
      fill(255, 30);
    } else {
      fill(255, 0, 100, 40);
    }
    // grab pixel position from corresponding hexagon
    drawHexagon(hexagons[this.x][this.y].pixelPos);
  }
  update() {
    // get current hexagon by x, y
    var curHex = hexagons[this.x][this.y];
    // increment or decrement activity
    // if creator and not double active
    if (this.creator) {
      if (curHex.nextActive < 2) {
        curHex.nextActive++;
      }
    }
    // if destroyer and active
    else {
      if (curHex.nextActive > 0) {
        curHex.nextActive--;
      }
    }
    // randomly chose direction -1 to 1
    this.dir += -1 + Math.floor(random(3));
    // make direction wrap around 0-5
    this.dir = wrap6(this.dir);
    // get next hexagon from current's neighbours
    var nextHex = curHex.neighbours[this.dir];
    // if next hexagon doesn't exist turn around
    if (nextHex === false) {
      this.dir = wrap6(this.dir + 3);
      nextHex = curHex.neighbours[this.dir];
      // if that doesn't work it's a corner
      // return and try again next round
      if (nextHex === false) return;
    }
    // update x and y from next hexagon
    this.x = nextHex.pos.x;
    this.y = nextHex.pos.y;
  }
}
// Hexagon Class
//======================================
class Hex {
  constructor(x, y) {
    // establish grid position
    this.pos = createVector(x, y);
    // establish pixel position
    this.pixelPos = createVector(0, 0);
    this.pixelPos.x = hexWidth * (1.5 * x + 0.5 + (y % 2) * 0.75);
    this.pixelPos.y = hexHeight * (y * 0.5 + 0.5);
    // establish state
    // active can be 0, 1, 2
    // double active results in double lines
    this.active = 0;
    this.nextActive = 0;
    // establish neighbours
    this.neighbours = [];
    // chose random layout (1-3) for dense (4/5/6 neighbours) display
    // regenerated when hex goes from inactive to active
    this.denseLayout = Math.ceil(random(3));
    // lazily updating count of active neighbours
    // used to colour hexagons
    this.zenosNeighbours = 0;
  }
  initialiseNeighbours(x, y) {
    // initialise neighbours called after all hexagons are constructed
    // because otherwise the hexagons array isn't full yet
    // lots of conditionals to allow for edge hexagons
    // start with array of falses
    let n = [false, false, false, false, false, false];
    const odd = y % 2;
    // above
    if (y >= 2) {
      n[0] = hexagons[x][y - 2];
    }
    // top right
    if (y >= 1) {
      if (!odd || x < columns - 1) {
        n[1] = hexagons[x + odd][y - 1];
      }
    }
    // bottom right
    if (y < rows - 1) {
      if (!odd || x < columns - 1) {
        n[2] = hexagons[x + odd][y + 1];
      }
    }
    // bottom
    if (y < rows - 2) {
      n[3] = hexagons[x][y + 2];
    }
    // bottom left
    if (y < rows - 1) {
      if (odd || x >= 1) {
        n[4] = hexagons[x - 1 + odd][y + 1];
      }
    }
    // top left
    if (y >= 1) {
      if (odd || x >= 1) {
        n[5] = hexagons[x - 1 + odd][y - 1];
      }
    }
    this.neighbours = n;
  }
  update() {
    // increment layout if hex is becoming active
    if (!this.active && this.nextActive) {
      this.denseLayout = this.denseLayout == 3 ? 1 : this.denseLayout + 1;
    }
    // update active from next active
    this.active = this.nextActive;
    // lazily update zenosNeighbours
    // zenosNeighbours lazily equals the amount of active neighbours (0-6)
    // plus the currect active state (0-2)
    if (this.zenosNeighbours == 0) {
      // make accurate if 0
      this.zenosNeighbours = this.countActiveNeighbours() + this.active;
    } else {
      this.zenosNeighbours =
        this.zenosNeighbours * (1 - zenoSway) +
        zenoSway * (this.countActiveNeighbours() + this.active);
    }
    // roughly check whether the mouse is inside the hexagon
    // update mouse target if so
    if (mousePos.dist(this.pixelPos) < hexRadius) {
      mouseTargetHex = this;
    }
  }
  countActiveNeighbours() {
    // returns number of active neighbours
    let activeNeighbours = 0;
    for (let i = 0; i < 6; i++) {
      if (this.neighbours[i] && this.neighbours[i].active) {
        activeNeighbours++;
      }
    }
    return activeNeighbours;
  }
  getActiveNeighbours() {
    // returns array of booleans for active neighbours
    let activeNeighbours = [];
    for (let i = 0; i < 6; i++) {
      // if neighbour exists and is active
      if (this.neighbours[i] && this.neighbours[i].active) {
        activeNeighbours.push(true);
      } else {
        activeNeighbours.push(false);
      }
    }
    return activeNeighbours;
  }
  drawHex() {
    // called in global draw
    noStroke();
    // even if drawHex is inactive we need to draw them blank
    // if drawGrid is active
    fill(0);
    let brightness = this.zenosNeighbours;
    if (drawHex && this.active) {
      fill(5 * brightness, 6 * Math.pow(brightness, 1.6), 16 * brightness);
    }
    drawHexagon(this.pixelPos);
  }
  drawLines() {
    // called in global draw
    push();
    translate(this.pixelPos.x, this.pixelPos.y);
    if (this.active) {
      // truthy
      let activeNeighboursCount = this.countActiveNeighbours();
      let activeNeighbours = this.getActiveNeighbours();
      stroke(255);
      strokeWeight(hexLineWeight);
      noFill();
      // no neighbours
      if (activeNeighboursCount == 0) {
        if (drawPoints && this.active == 2) {
          ellipse(0, 0, hexDoubleLineOffset);
        }
      }
      // one neighbour
      else if (activeNeighboursCount == 1) {
        let activeEdge = activeNeighbours.indexOf(true);
        let activeNeighbour = this.neighbours[activeEdge];
        // if it is double active
        // or the active neighbour is double active
        if (activeNeighbour.active == 2 || this.active == 2) {
          // if drawPoints is inactive the neighbour must have > 1 active neighbour
          // to avoid ellipses on an active edge
          if (drawPoints || activeNeighbour.countActiveNeighbours() > 1) {
            // get two edge points
            var pos1 = getEdgePos(activeEdge, 1);
            var pos2 = getEdgePos(activeEdge, -1);
            // get two control points
            var control1 = createVector(
              hexDoubleLineOffset * 0.5,
              -hexHeight / 2 + hexDoubleLineOffset
            ).rotate((activeEdge * Math.PI) / 3);
            var control2 = createVector(
              -hexDoubleLineOffset * 0.5,
              -hexHeight / 2 + hexDoubleLineOffset
            ).rotate((activeEdge * Math.PI) / 3);
            // draw bezier curve for arc cap
            beginShape();
            vertex(pos1.x, pos1.y);
            bezierVertex(
              control1.x,
              control1.y,
              control2.x,
              control2.y,
              pos2.x,
              pos2.y
            );
            endShape();
          }
        }
      }
      // two or three neighbours
      else if (activeNeighboursCount == 2 || activeNeighboursCount == 3) {
        // link up all the active neighbours
        for (var i = 0; i < 6; i++) {
          if (activeNeighbours[i]) {
            for (var j = i + 1; j < 6; j++) {
              if (activeNeighbours[j]) {
                this.drawCurveBetweenEdges(i, j);
              }
            }
          }
        }
      }
      // four neighbours
      else if (activeNeighboursCount == 4) {
        // get the index of each inactive edge
        let skipped1 = activeNeighbours.indexOf(false);
        let skipped2 =
          activeNeighbours.slice(skipped1 + 1).indexOf(false) + skipped1 + 1;
        // make list of active edge positions
        // making sure to loop from the most clockwise edge to avoid 0/5 problem
        var positions = [];
        let skippedClockwise = skipped1 == 0 ? skipped1 : skipped2;
        for (let i = skippedClockwise; i < skippedClockwise + 6; i++) {
          if (wrap6(i) != skipped1 && wrap6(i) != skipped2) {
            positions.push(wrap6(i));
          }
        }
        // skips are adjacent
        if (
          skipped2 == wrap6(skipped1 + 1) ||
          (skipped1 == 0 && skipped2 == 5)
        ) {
          if (this.denseLayout == 3) {
            // connect edges to adjacent edges, ignore straight line
            this.drawCurveBetweenEdges(positions[0], positions[1]);
            this.drawCurveBetweenEdges(positions[1], positions[2]);
            this.drawCurveBetweenEdges(positions[2], positions[3]);
          } else if (this.denseLayout == 2) {
            // cross over curves
            this.drawCurveBetweenEdges(positions[0], positions[2]);
            this.drawCurveBetweenEdges(positions[1], positions[3]);
          } else {
            // pair edges with adjacent edges
            this.drawCurveBetweenEdges(positions[0], positions[1]);
            this.drawCurveBetweenEdges(positions[2], positions[3]);
          }
        }
        // 1 and 3 situation
        // or 2 and 2
        else {
          if (this.denseLayout == 3) {
            // connect edges to adjacent edges
            this.drawCurveBetweenEdges(positions[0], positions[1]);
            this.drawCurveBetweenEdges(positions[1], positions[2]);
            this.drawCurveBetweenEdges(positions[2], positions[3]);
            this.drawCurveBetweenEdges(positions[3], positions[0]);
          } else if (this.denseLayout == 2) {
            // pair edges with adjacent edges
            this.drawCurveBetweenEdges(positions[3], positions[0]);
            this.drawCurveBetweenEdges(positions[1], positions[2]);
          } else {
            // pair edges with opposite adjacent edges
            this.drawCurveBetweenEdges(positions[0], positions[1]);
            this.drawCurveBetweenEdges(positions[2], positions[3]);
          }
        }
      }
      // five neighbours
      else if (activeNeighboursCount == 5) {
        let skipped = activeNeighbours.indexOf(false);
        if (this.denseLayout == 3) {
          // connect edges to adjacent edges
          for (var i = skipped; i < 5 + skipped; i++) {
            var edge1 = i == skipped ? i + 5 : i;
            this.drawCurveBetweenEdges(edge1, i + 1);
          }
        } else if (this.denseLayout == 2) {
          // batman logo
          // curve between the two skipped-adjacent edges
          this.drawCurveBetweenEdges(skipped + 1, skipped + 5);
          // connect other 3 to eachother
          this.drawCurveBetweenEdges(skipped + 2, skipped + 3);
          this.drawCurveBetweenEdges(skipped + 3, skipped + 4);
        } else if (this.denseLayout == 1) {
          // evil M
          // curve the two skipped-adjacent edges to the skipped-opposite edge
          this.drawCurveBetweenEdges(skipped + 1, skipped + 3);
          this.drawCurveBetweenEdges(skipped + 5, skipped + 3);
          // curve the other two edges to the skipped-adjacent edges
          this.drawCurveBetweenEdges(skipped + 1, skipped + 2);
          this.drawCurveBetweenEdges(skipped + 5, skipped + 4);
        }
      }
      // 6 neighbours
      else {
        if (this.denseLayout == 3) {
          // connect edges to adjacent edges
          for (var i = 0; i < 6; i++) {
            this.drawCurveBetweenEdges(i, i + 1);
          }
        } else {
          // pair edges with adjacent edges
          // alternate using denseLayout == 2 or 1
          for (var i = this.denseLayout - 1; i < 6; i += 2) {
            this.drawCurveBetweenEdges(i, i + 1);
          }
        }
      }
    }
    pop();
  }
  drawCurveBetweenEdges(edge1, edge2) {
    // called by drawLines()
    // used to determine whether they should be single, double, or diverging
    // also used to set curve offsets for inner/outer lines
    // make sure edges are between 0-5
    edge1 = wrap6(edge1);
    edge2 = wrap6(edge2);
    // should we draw it as a double line?
    let double = false;
    // if the tile is double active
    if (this.active == 2) double = true;
    // if both of the edge tiles exist and are double active
    if (
      this.neighbours[edge1] &&
      this.neighbours[edge1].active == 2 &&
      this.neighbours[edge2] &&
      this.neighbours[edge2].active == 2
    ) {
      double = true;
    }
    if (double) {
      // set outer control point slightly further than offset width
      // to create even margin
      // cos bezier curves, son
      this.drawCurveWithOffset(edge1, edge2, 1, 1, -hexDoubleLineOffset * 0.8);
      this.drawCurveWithOffset(edge1, edge2, -1, -1, hexDoubleLineOffset * 0.5);
    }
    // if tile is single active
    // and not both of the edges are double active
    else {
      // if edge1 hexagon exists and is double active
      if (this.neighbours[edge1] && this.neighbours[edge1].active == 2) {
        // use half offset width for midpoint of diverging lines
        // set outer control point slightly further to create even margin
        this.drawCurveWithOffset(
          edge1,
          edge2,
          1,
          0,
          -hexDoubleLineOffset * 0.4
        );
        this.drawCurveWithOffset(
          edge1,
          edge2,
          -1,
          0,
          hexDoubleLineOffset * 0.25
        );
      }
      // if edge2 hexagon exists and is double active
      else if (this.neighbours[edge2] && this.neighbours[edge2].active == 2) {
        // use half offset width for midpoint between single and double
        // set outer control point slightly further to create even margin
        this.drawCurveWithOffset(
          edge1,
          edge2,
          0,
          1,
          -hexDoubleLineOffset * 0.4
        );
        this.drawCurveWithOffset(
          edge1,
          edge2,
          0,
          -1,
          hexDoubleLineOffset * 0.25
        );
      }
      // if everything is single
      else {
        this.drawCurveWithOffset(edge1, edge2, 0, 0);
      }
    }
  }
  drawCurveWithOffset(edge1, edge2, offset1, offset2, originOffset) {
    // called by drawCurveBetweenEdges()
    // determines which is the inner and outer line
    // sets offset and draws line accordingly
    // originOffset is the distance we move the origin point
    // in the opposite direction of the average angle of the two points
    let origin = createVector(0, 0);
    if (originOffset) {
      origin.y = originOffset;
    }
    // set up positions as per offsets
    let pos1 = getEdgePos(edge1, offset1);
    let pos2 = getEdgePos(edge2, offset2);
    // if edge 2 is one clockwise from edge 1
    if (edge1 == wrap6(edge2 - 1)) {
      // flips offset 2
      pos2 = getEdgePos(edge2, -offset2);
      // brings offset in smooth curve
      origin.y -= hexRadius * 0.25;
      origin.rotate(((edge1 + 0.5) * Math.PI) / 3);
    }
    // if edge 2 is one anti-clockwise from edge 1
    else if (edge1 == wrap6(edge2 + 1)) {
      // flips offset 1
      pos1 = getEdgePos(edge1, -offset1);
      // brings offset in smooth curve
      origin.y -= hexRadius * 0.25;
      origin.rotate(((edge1 - 0.5) * Math.PI) / 3);
    }
    // if edge 2 is two clockwise from edge 1
    else if (edge1 == wrap6(edge2 - 2)) {
      // flips offset 2
      pos2 = getEdgePos(edge2, -offset2);
      origin.rotate(((edge1 + 1) * Math.PI) / 3);
    }
    // if edge 2 is two anti-clockwise from edge 1
    else if (edge1 == wrap6(edge2 + 2)) {
      // flips offset 1
      pos1 = getEdgePos(edge1, -offset1);
      origin.rotate(((edge1 - 1) * Math.PI) / 3);
    }
    // if edges are opposites
    // using the line function everything is 1px off
    // so we just use the quadratic bezier
    if (Math.abs(edge2 - edge1) == 3) {
      // flip the offset 2 to create parallel lines
      pos2 = getEdgePos(edge2, -offset2);
      // reset origin offset so line is straight
      origin.y =
        (hexDoubleLineOffset *
          0.5 *
          (offset1 + offset2) *
          0.5 *
          (edge1 - edge2)) /
        3;
      origin.rotate(((edge1 + 1.5) * Math.PI) / 3);
    }
    // draw the line
    beginShape();
    vertex(pos1.x, pos1.y);
    quadraticVertex(origin.x, origin.y, pos2.x, pos2.y);
    endShape();
  }
}
// Mouse Events
//======================================
function drawMouseHexagon() {
  fill(255, 50);
  if (mouseTargetHex && mouseOnScreen()) {
    drawHexagon(mouseTargetHex.pixelPos);
  }
}
function mousePressed() {
  if (mouseTargetHex && mouseOnScreen()) {
    // loop between 0 -2
    // increment for left mouse button
    if (mouseButton == LEFT) {
      mouseTargetHex.nextActive = (mouseTargetHex.nextActive + 1) % 3;
    }
    // decrement for right mouse button
    else if (mouseButton == RIGHT) {
      mouseTargetHex.nextActive = (mouseTargetHex.nextActive - 1) % 3;
    }
    // update last mouse hex
    mouseLastHex = mouseTargetHex;
  }
}
function mouseDragged() {
  // if it exists and is on screen
  // if it hasn't just been updated (mousePressed)
  // if it's a different hex from the last updated one
  if (
    mouseTargetHex &&
    mouseOnScreen() &&
    mouseTargetHex.nextActive == mouseTargetHex.active &&
    mouseLastHex != mouseTargetHex
  ) {
    // increment for left mouse button
    if (mouseButton == LEFT && mouseTargetHex.nextActive < 2) {
      mouseTargetHex.nextActive++;
    }
    // decrement for right mouse button
    else if (mouseButton == RIGHT && mouseTargetHex.nextActive > 0) {
      mouseTargetHex.nextActive--;
    }
    // update last mouse hex
    mouseLastHex = mouseTargetHex;
  }
}

document.addEventListener("DOMContentLoaded", function () {
  function updateStepper(step, processId) {
    console.log(step);
    const stepperMessage = document.getElementById("stepperMessage");
    stepperMessage.innerHTML = `Step ${step}`;
    for (let i = 1; i <= 6; i++) {
      const stepElement = document.getElementById(`step${i}`);
      if (i <= step) {
        stepElement.classList.add("active");
      } else {
        stepElement.classList.remove("active");
      }
    }

    if (step === 2) {
      document.getElementById("educationWarning").classList.remove("hidden");
    } else {
      //document.getElementById("educationWarning").classList.add("hidden");
    }
    if (step === 6) {
      const select = document.getElementById("companySelect");
      const selected = select.options[select.selectedIndex].text;
      window.location = `/view/${selected.trim().toLowerCase()}/${processId}`;
    }
  }
  const adminButton = document.getElementById("adminButton");
  if (adminButton) {
    adminButton.addEventListener("click", function () {
      window.location = "/admin";
    });
  }
  const searchButton = document.getElementById("goButton");
    if (searchButton) {
      searchButton.addEventListener("click", function () {
        searchButton.classList.add("hidden");
        const stepper = document.getElementById("stepper");
        stepper.classList.remove("hidden");

        const searchInput = document.getElementById("questionInput");
        const question = searchInput.value;
        const companySelect = document.getElementById("companySelect");
        const company = companySelect.options[companySelect.selectedIndex].text;
        const data = {
          question: question,
          company: company,
        };
        fetch("/process", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(data),
        })
          .then((response) => {
            if (response.ok) {
              return response.json();
            }
            throw new Error("Network response was not ok.");
          })
          .then((data) => {
            console.log(data);
            const eventSource = new EventSource("/progress/" + data.uid);
            const dd = data.uid;
            eventSource.onmessage = function (event) {
              const data = JSON.parse(event.data);
              updateStepper(data.step, dd);
            };
            eventSource.onerror = function (event) {
              console.error("EventSource failed:", event);
            };
          })
          .catch((error) => {
            console.error(
              "There has been a problem with your fetch operation:",
              error
            );
          });
      });
    }
});
