
//Popper.js Initialization
const popperButton = document.querySelector("#popper-button");
const popperPopup = document.querySelector("#popper-popup");
const popperArrow = document.querySelector("#popper-arrow");

let popperInstance = null;

//create popper instance
function createInstance() {
    popperInstance = Popper.createPopper(popperButton, popperPopup, {
        placement: "bottom", //preferred placement of popper
        modifiers: [
            {
                name: "offset", //offsets popper from the reference/button
                options: {
                    offset: [0, 8]
                }
            },
            {
                name: "flip", //flips popper with allowed placements
                options: {
                    allowedAutoPlacements: ["right", "left", "top", "bottom"],
                    rootBoundary: "viewport"
                }
            }
        ]
    });
}

//destroy popper instance
function destroyInstance() {
    if (popperInstance) {
        popperInstance.destroy();
        popperInstance = null;
    }
}

//show and create popper
function showPopper() {
    popperPopup.setAttribute("show-popper", "");
    popperArrow.setAttribute("data-popper-arrow", "");
    createInstance();
}

//hide and destroy popper instance
function hidePopper() {
    popperPopup.removeAttribute("show-popper");
    popperArrow.removeAttribute("data-popper-arrow");
    destroyInstance();
}

//toggle show-popper attribute on popper to hide or show it with CSS
function togglePopper() {
    if (popperPopup.hasAttribute("show-popper")) {
        hidePopper();
    } else {
        showPopper();
    }
}
//execute togglePopper function when clicking the popper reference/button
popperButton.addEventListener("click", function (e) {
    e.preventDefault();
    togglePopper();
});


