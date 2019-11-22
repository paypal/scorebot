// drop down for side bar
var dropdown = document.getElementsByClassName("dropdown-btn");
var i;

for (i = 0; i < dropdown.length; i++) {
  dropdown[i].addEventListener("click", function() {
    this.classList.toggle("active");
    var dropdownContent = this.nextElementSibling;
    if (dropdownContent.style.display === "block") {
      dropdownContent.style.display = "none";
    } else {
      dropdownContent.style.display = "block";
    }
  });
}
// hamburger menu 
function hamburger() {
  var sidebar = document.getElementById("daSidebar");
  if (sidebar.className === "sidebar") {
    sidebar.className += " responsive";
  } else {
    sidebar.className = "sidebar";
  }

  var overlay = document.getElementById("daOverlay");
    if (overlay.className === "overlay") {
    overlay.className += " responsive";
  } else {
    overlay.className = "overlay";
  }
}

function closeHamburger() {
  var x = document.getElementById("daSidebar");
  if (x.className === "sidebar responsive") {
    x.className = "sidebar";
  } else {
    x.className = "sidebar responsive";
  }

  var overlay = document.getElementById("daOverlay");
    if (overlay.className === "overlay responsive") {
    overlay.className = "overlay";
  } else {
    overlay.className = "overlay responsive";
  }
}