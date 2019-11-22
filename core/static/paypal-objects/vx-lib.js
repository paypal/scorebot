/*! vxpattern-lib-paypal | Version: 3.1.0 | Built from github.paypal.com/ConsumerWeb-UI/vxpattern-lib-paypal */

(function (win, doc, undefined) {
	'use strict';

	/**
	 * Build the global VX object
	 */
	if (!win.VX) {
		win.VX = {};
	}

	/**
	 * Build feature detection object
	 */
	win.VX.featDetection = {
		hasFocusIn: !!("onfocusin" in win),
		hasPlaceholder: typeof doc.createElement('input').placeholder === 'string',
		hasTransition: doc.body.style.transition === ''
	};

	/**
	 * Build noop object functions
	 */
	win.VX.noopObj = { // Used for knowing what to return focus to upon closing
		focus: function noop() {}, // noop to prevent thing is not a function crash
		addEventListener: function noop() {} // noop to prevent thing is not a function crash
	};

}(window, document));


;// End of file

/**
 * JS component for handling the behavior of  global nav events
 */

(function (win, doc, undefined) {
	'use strict';

	/**
	 * Store the main mobile menu trigger, overlay and global nav elements
	 */
	var root = document.body,
		mobileMenuTrigger = doc.querySelector('.vx_globalNav-toggleTrigger') || win.VX.noopObj,
		mobileOverlayTrigger = doc.querySelector('.vx_globalNav-overlay') || win.VX.noopObj,
		globalNavContainer = doc.querySelector('.vx_globalNav-container') || win.VX.noopObj;

	function toggleMobileNav() {
		var hasOpenNav = doc.body.classList.contains('vx_hasOpenNav');

		if (!hasOpenNav) {
			doc.body.classList.add('vx_hasOpenNav');
			globalNavContainer.focus();
		} else {
			doc.body.classList.remove('vx_hasOpenNav');
			mobileMenuTrigger.focus();
		}
	}

	/**
	 * Event listener for the mobile menu trigger
	 */
	mobileMenuTrigger.addEventListener('click', toggleMobileNav);

	/**
	 * Event listener for the overlay that covers the main content area when mobile menu is open
	 */
	mobileOverlayTrigger.addEventListener('click', toggleMobileNav);

	/**
	 * @function - adds `keyup` event listener to container element
	 *
	 * Note: listens for ESC key only
	 */
	root.addEventListener('keyup', function (event) {
		var openModal = {};

		if (event.keyCode === 27 && // Is key Esc key?
			root.className.indexOf('vx_hasOpenNav') !== -1) { // Is modal open?

			// Grab the open modal
			toggleMobileNav();
		}
	});

}(window, document));


;// End of file

(function (win, doc, undefined) {
	'use strict';

	/**
	 * Grab the main parent element for event delegation, rather than
	 * attaching an event listener to each individual floating label instance.
	 */
	var root = doc.getElementById('vx_root') || document.body;


	/** *******************************
	 * GENERIC REUSABLE DOM FUNCTIONS
	 */

	/**
	 * @function identifyParentElement - crawls up the DOM to find a needed parent
	 * @param {Object} params - required; configuration object
	 * @param {Object} params.child - required; the root child, DOM element
	 * @param {string} params.className - required; the needed parent's class name
	 * @param {number} params.maxLevels - optional; the maximum number of parent lookups
	 * @param {function} params.callback - required; callback because the DOM is async
	 * @param {number} currentLevel - internal only; counts the level-ups
	 */
	function identifyParentElement(params, currentLevel) {
		var el = params.child.parentElement,
			className = params.className,
			callback = params.callback,
			maxLevels = params.maxLevels || 2;

		/**
		 * Original call should be undefined, so provide a default of 1
		 * If recursively called, ++ the value
		 */
		currentLevel = currentLevel || 1;

		if (!el) {
			// Bail early
			callback(false);

		} else if (el.className.indexOf && el.className.indexOf(className) === -1 &&
			currentLevel <= maxLevels) {

			identifyParentElement({
					child: el,
					className: className,
					callback: callback,
					maxLevels: maxLevels
				},
				currentLevel++);

		} else if (el.className.indexOf && el.className.indexOf(className) === -1 &&
			currentLevel > maxLevels) {

			callback(false); // call with false as parent wasn't found

		} else {
			callback(true, el);
		}
	}


	/** *******************************
	 * INPUT FUNCTIONALITY
	 */

	function focusInCb(event) {
		var target = event.target;
		/**
		 * Test if the target was an input, and not a textarea or another element
		 */
		if (target && target.tagName.toUpperCase() === 'INPUT') {
			/**
			 * Find out if parent or grandparent has the vx_floatingLabel class
			 */
			identifyParentElement({
				child: target,
				className: 'vx_floatingLabel',
				maxLevels: 2,
				callback: function (hasClass, el) {
					if (hasClass) {
						/**
						 * Add the focus class remove value class if present
						 */
						el.classList.remove('hasValue');
						el.classList.add('hasFocus');
					}
				}
			});
		} else if (target && target.tagName.toUpperCase() === 'SELECT') {
			/**
			 * Find out if parent or grandparent has the vx_floatingLabel class
			 */
			identifyParentElement({
				child: target,
				className: 'vx_floatingLabel',
				maxLevels: 2,
				callback: function (hasClass, el) {
					if (hasClass) {
						/**
						 * Add the focus class
						 */
						el.classList.add('hasFocus');
					}
				}
			});
		}
	}
	function focusOutCb(event) {
		var target = event.target;
		/**
		 * Check if element is a text input
		 */
		if (target && target.tagName.toUpperCase() === 'INPUT') {
			/**
			 * Find out if parent or grandparent has the vx_floatingLabel class
			 */
			identifyParentElement({
				child: target,
				className: 'vx_floatingLabel',
				maxLevels: 2,
				callback: function (hasClass, el) {
					if (hasClass) {
						/**
						 * Does target have a value?
						 * If so, add value class remove focus class
						 */
						if (target.value) {
							el.classList.add('hasValue');
							el.classList.remove('hasFocus');
						} else {
							/**
							 * If no, remove the value and focus class
							 */
							el.classList.remove('hasValue');
							el.classList.remove('hasFocus');
						}
					}
				}
			});
		/**
		 * Check if element is a select input
		 */
		} else if (target && target.tagName.toUpperCase() === 'SELECT') {
			/**
			 * Find out if parent or grandparent has the vx_floatingLabel class
			 */
			identifyParentElement({
				child: target,
				className: 'vx_floatingLabel',
				maxLevels: 2,
				callback: function (hasClass, el) {
					if (hasClass) {
						/**
						 * Add the focus class
						 */
						el.classList.remove('hasFocus');
					}
				}
			});
		}
	}

	if (VX.featDetection.hasFocusIn) {
		root.addEventListener('focusin', focusInCb);
		root.addEventListener('focusout', focusOutCb);
	} else {
		root.addEventListener('focus', focusInCb, true);
		root.addEventListener('blur', focusOutCb, true);
	}

	/**
	 *	Floating labels could have a default value and this functions updates the state of
	 *	labels which has value.
	 * @param scope {object} - optional: DOM element to restrict query
	 */
	function evaluateFloatingLabels(scope) {
		var context = scope || doc,
			inputElements = context.querySelectorAll('.vx_floatingLabel input'),
			i = 0,
			len = inputElements.length;

		for (i; i < len; i++) {
			/**
			 * Append 'hasValue' CSS class
			 */
			updateFloatingLabelState(inputElements[i]);
		}
	}

	/**
	 *	This function avoids the JS lint warning of adding "identifyParentElement" in a loop.
	 *
	 *	@param inputEl {object} - required; Expects this to be an input element DOM type
	 */
	function updateFloatingLabelState(inputEl) {
		identifyParentElement({
			child: inputEl,
			className: 'vx_floatingLabel',
			maxLevels: 2,
			callback: function (hasClass, el) {
				if (hasClass) {
					/**
					 * Does target have a value?
					 * If so, add hasValue class
					 */
					if (inputEl && inputEl.value && inputEl.value !== '') {
						el.classList.add('hasValue');
					} else {
						/**
						 * If no, remove the hasValue class
						 */
						el.classList.remove('hasValue');
					}

					/**
					 *	Makes every Floating element an active one
					 */

					el.classList.add('vx_floatingLabel_active');
					el.classList.remove('vx_floatingLabel');
				}
			}
		});
	}

	if (!win.VX) {
		console.error('Error: the component `core.js` is required.');
	} else if (!win.VX.inputsSelects) {
		win.VX.inputsSelects = {};
	}
	/**
	 * Expose evaluateFloatingLabels for programmatic control
	 */
	win.VX.inputsSelects.evaluateFloatingLabels = evaluateFloatingLabels;
	/**
	 * Execute on bootstrap of JS for initial load
	 */
	evaluateFloatingLabels();
}(window, document));


;// End of file

/**
 * JS component for handling the behavior of the modal feature
 */
(function (win, doc, undefined) {
	'use strict';

	/**
	 * Grab the main parent element for event delegation, rather than
	 * attaching an event listener to each individual floating label instance.
	 */
	var root = doc.getElementById('vx_root') || document.body,
	/**
	 * The multiple attempts here to grab the appropriate element are because of browser inconsistencies
	 * `scrollTopEl` is used here anytime `scrollTop` is used.
	 */
		scrollTopEl = document.documentElement ||
			document.body.parentNode ||
			document.body,
		openingTriggerEl = null; // For caching the trigger element that opens modal

	function openVxModal(modalId) {
		/**
		 * Grab scroll position for preserving during modal operations.
		 */
		var scrollPos = scrollTopEl.scrollTop,
			modalEl = doc.getElementById(modalId),
			modalBg = doc.getElementById('vx_modal-background'),
			globalNavContainer = doc.querySelector('.vx_globalNav-main'),
			foregroundContainer = doc.querySelector('.vx_foreground-container');
		/**
		 * @function finishTransition - responsible for cleaning up after transitions
		 */
		function finishTransition() {
			/**
			 * Preserve the original scroll position by positioning the element with `top` prop
			 */
			doc.querySelector('.vx_foreground-container').setAttribute('style', 'top: -' + scrollPos + 'px;');
			/**
			 * Save the scroll position to the body for later retrieval
			 */
			root.setAttribute('data-scroll-position', scrollPos);
			/**
			 * Set the scroll position to 0 to ensure the top of the modal is visible,
			 * if the view was scrolled down to click on the trigger
			 */
			scrollTopEl.scrollTop = 0;
			/**
			 * Add and remove the appropriate classes
			 */
			root.classList.add('vx_hasOpenModal');
			modalEl.classList.remove('vx_modalIsOpening');
			modalEl.classList.add('vx_modalIsOpen');
			/**
			 * Remove event listener.
			 */
			modalEl.removeEventListener('transitionend', finishTransition);
			/**
			 * Focus on modal container
			 */
			modalEl.focus();
			/**
			 * This adds the inert attribute to the global nav and the foreground container
			 * This is for removing the non-modal elements from assistive technologies,
			 * aka "focus trapping"
			 *
			 * This currently depends on the polyfill seen here: https://github.com/WICG/inert.
			 * This is packaged up with this library if you use the whole built js file in dist.
			 */
			if (globalNavContainer && globalNavContainer.setAttribute) {
				globalNavContainer.setAttribute('inert', true);
				globalNavContainer.setAttribute('aria-hidden', true);
			}
			if (foregroundContainer && foregroundContainer.setAttribute) {
				foregroundContainer.setAttribute('inert', true);
				foregroundContainer.setAttribute('aria-hidden', true);
			}
		}

		/**
		 * Add the background to the body, if needed
		 */
		if (!modalBg) {
			modalBg = doc.createElement('div');
			modalBg.setAttribute('class', 'vx_modal-background vx_modalPrepBg');
			modalBg.setAttribute('id', 'vx_modal-background');
			root.appendChild(modalBg);
		} else {
			modalBg.classList.add('vx_modalPrepBg');
		}
		/**
		 * Prep the modal for animation. I.e. add change from `display: none`
		 */
		modalEl.classList.add('vx_modalPrepToOpen');
		/**
		 * What for DOM to update and register new `display` prop for both modal and BG
		 */
		setTimeout(function () {
			modalEl.classList.add('vx_modalIsOpening');
			modalBg.classList.add('vx_modalBgIsShown');
			/**
			 * Add minimal a11y support in case no aria describedby is used
			 */
			if (!modalEl.hasAttribute('aria-label')) {
				modalEl.setAttribute('aria-label', 'Modal Dialog');
			}
		}, 35);
		/**
		 * Does client have transitionEnd event?
		 * If not, fallback to setTimeout
		 */
		if (VX.featDetection.hasTransition) {
			modalEl.addEventListener('transitionend', finishTransition);
		} else {
			setTimeout(finishTransition, 220);
		}
	}
	/**
	 * @function closeVxModal â€“ the function that handles closing the modal,
	 * used for both event and programmatic control
	 * @param {string} modalId
	 * @param {string} elSelectorToReceiveFocus â€“ optional, pass in selector for element that receives
	 * focus once the modal is closed. A11y!
	 */
	function closeVxModal(modalId, elSelectorToReceiveFocus) {
		/**
		 * Grab original scroll position before opening the modal.
		 * Grab modal reference or just grab the current open modal element.
		 */
		var scrollPos = root.getAttribute('data-scroll-position'),
			modalEl = modalId ? doc.getElementById(modalId) : doc.querySelector('.vx_modalIsOpen'),
			modalBg = doc.getElementById('vx_modal-background'),
			globalNavContainer = doc.querySelector('.vx_globalNav-main'),
			foregroundContainer = doc.querySelector('.vx_foreground-container');
		/**
		 * @function finishTransition - responsible for cleaning up after transitions
		 */
		function finishTransition() {
			var elForFocus = openingTriggerEl || // Assign trigger
				( elSelectorToReceiveFocus && doc.querySelector(elSelectorToReceiveFocus) ) || // Or, assign selector
				win.VX.noopObj; // Finally, assign noop if none exist
			/**
			 * Remove the "faked" scroll position
			 */
			doc.querySelector('.vx_foreground-container').removeAttribute('style');
			/**
			 * Grab the original scroll position and add it back to the body
			 */
			root.removeAttribute('data-scroll-position');
			scrollTopEl.scrollTop = scrollPos;
			/**
			 * Add and remove the appropriate classes
			 */
			modalEl.classList.remove('vx_modalIsClosing');
			modalEl.classList.remove('vx_modalPrepToOpen');
			modalBg.classList.remove('vx_modalPrepBg');
			/**
			 * Remove event listener.
			 */
			modalEl.removeEventListener('transitionend', finishTransition);
			elForFocus.focus(); // place focus back on original triggering element
			openingTriggerEl = null; // Empty trigger element
		}
		/**
		 * This adds the inert attribute to the global nav and the foreground container
		 * This is for removing the non-modal elements from assistive technologies,
		 * aka "focus trapping"
		 *
		 * This currently depends on the polyfill seen here: https://github.com/WICG/inert.
		 * This is packaged up with this library if you use the whole built js file in dist.
		 */
		if (globalNavContainer && globalNavContainer.removeAttribute) {
			globalNavContainer.removeAttribute('inert', true);
			globalNavContainer.removeAttribute('aria-hidden', true);
		}
		if (foregroundContainer && foregroundContainer.removeAttribute) {
			foregroundContainer.removeAttribute('inert', true);
			foregroundContainer.removeAttribute('aria-hidden', true);
		}
		/**
		 * Prep body and modal for close animation
		 */
		root.classList.remove('vx_hasOpenModal');
		modalEl.classList.remove('vx_modalIsOpen');
		modalBg.classList.remove('vx_modalBgIsShown');
		modalEl.classList.add('vx_modalIsClosing');
		/**
		 * Does client have transitionEnd event?
		 */
		if (VX.featDetection.hasTransition) {
			modalEl.addEventListener('transitionend', finishTransition);
		} else {
			setTimeout(finishTransition, 220);
		}
	}
	/**
	 * @function - adds `click` event listener to container element
	 *
	 * Note: Uses "event delegation" to conserve memory and handle dynamic elements
	 */
	root.addEventListener('click', function (event) {
		var className = event.target.className,
			modalId;
		/**
		 * Are we clicking on a trigger to open or close modal?
		 *
		 * Note: check for existence of `indexOf` to prevent errors when clicking SVGs
		 */
		if (className.indexOf) {
			if (className.indexOf('vx_modal-trigger') !== -1) {
				modalId = event.target.getAttribute('data-modal-id');
				openingTriggerEl = event.target;
				openVxModal(modalId);
			}
			if (className.indexOf('vx_modal-dismiss_trigger') !== -1 ||
				className.indexOf('vx_modal-dismiss_x-trigger') !== -1) {
				modalId = event.target.getAttribute('data-modal-id');
				closeVxModal(modalId);
			}
		}
	});
	/**
	 * @function - adds `keyup` event listener to container element
	 *
	 * Note: listens for ESC key only
	 */
	root.addEventListener('keyup', function (event) {
		var openModal = {};

		if (event.keyCode === 27 && // Is key Esc key?
			root.className.indexOf('vx_hasOpenModal') !== -1) { // Is modal open?

			// Grab the open modal
			openModal = doc.querySelector('.vx_modalIsOpen');
			// If the X button has `-trigger` appended to it, we control it
			if (openModal.querySelector('.vx_modal-dismiss_x-trigger')) {
				// Since we control it, let's close it!
				closeVxModal();
			}
		}
	});

	if (!win.VX) {
		console.error('Error: the component `core.js` is required.');
	} else if (!win.VX.modal) {
		win.VX.modal = {};
	}
	/**
	 * Expose open and close for programmatic control
	 */
	win.VX.modal.open = openVxModal;
	win.VX.modal.close = closeVxModal;
}(window, document));


;// End of file

/**
 * JS component for handling the behavior of the Overflow Menu
 */
(function (win, doc, undefined) {
	'use strict';

	var root = doc.getElementById('vx_root') || document.body;

	/* function to open the menu */
	function openMenu(menu) {
		menu.nextElementSibling.classList.add('vx_overflowMenuIsOpen');
		menu.classList.add('active');
		menu.focus();
	}

	/* function to close the menu */
	function closeMenu (menu) {
		menu.nextElementSibling.classList.remove('vx_overflowMenuIsOpen');
		menu.classList.remove('active');
		menu.focus();
	}

	/* event listener for the menu button handles the closing and opening of menu */
	root.addEventListener('click', function catchEvent(event) {
		var target = event.target.className.indexOf('vx_overflowMenu-btn') === -1 ? event.target.parentElement : event.target,
			btnIndex = target.className.indexOf('vx_overflowMenu-btn'),
			btnOpen = target.nextElementSibling ? target.nextElementSibling.className.indexOf('vx_overflowMenuIsOpen') : 0 ,
			isMenuOpen = doc.querySelector('.vx_overflowMenuIsOpen') ,
			btnOpenActive = doc.querySelector('.vx_overflowMenu-btn.active');
		if (btnIndex !== -1) {
			if (btnOpen === -1) {
				closeOtherMenu(target, isMenuOpen, btnOpenActive);
			}
			else {
				closeMenu(target);
			}
		} else if (isMenuOpen) {
			closeMenu(btnOpenActive);
		}
	});

	/* function to close the other menu which may be open before opening a new menu */
	function closeOtherMenu(target, isMenuOpen, btnOpenActive) {
		if (isMenuOpen) {
			closeMenu(btnOpenActive);
		}
		openMenu(target);
	}

	/* event listener for esc key to close the menu */
	root.addEventListener('keyup', function (event) {
		var isMenuOpen = doc.querySelector('.vx_overflowMenuIsOpen'),
		btnOpen = doc.querySelector('.vx_overflowMenu-btn.active');
		if (event.keyCode === 27 && isMenuOpen) {
			closeMenu(btnOpen);
		}
	});
})(window, document);


;// End of file

/**
 * @IIFE transition to a flow animation
 * This provides the fade out and fade in for transition between flows
 */
(function (win, doc, undefined) {
	'use strict';

	var root = doc.getElementById('vx_root') || document.body;

	function startFlow() {
		var el = document.querySelector('.vx_addFlowTransition');
		el.classList.add('vx_hasFadeTransition');
	}
	function endFlow() {
		var el = document.querySelector('.vx_addFlowTransition');
		el.classList.remove('vx_hasFadeTransition');
	}
	function bindFlowListener() {
		root.addEventListener('click', function (event) {
			var target = event.target;
			if (target.className.indexOf && target.className.indexOf('vx_flowTrigger') !== -1) {
				startFlow();
			}
		});
	}

	if (root.className.indexOf && root.className.indexOf('vx_hasFadeTransition') !== -1) {
		bindFlowListener();
		setTimeout(function () {
			endFlow();
		}, 35);
	} else if (document.querySelector('.vx_addFlowTransition')) {
		bindFlowListener();
	}

	if (!win.VX) {
		console.error('Error: the component `core.js` is required.');
	} else if (!win.VX.transitions) {
		win.VX.transitions = {};
	}

	win.VX.transitions.startFlow = startFlow;
}(window, document));

/**
 * @IIFE stepped animation functionality
 * This provides the animation for stepping through a flow
 */
(function (win, doc, undefined) {
	'use strict';

	function measureElHeight(el, callback) {
		var elHeight;

		// Quickly rendering to DOM to measure height and width.
		// Then, removing it.
		el.classList.add('vx_invisiblyRender');
		elHeight = el.offsetHeight;
		el.classList.remove('vx_invisiblyRender');

		callback(elHeight);
	}
	function slideToStep(container, currentStep, requestedStep) {
		var animatingEl = container.firstElementChild,
			slides = animatingEl.querySelectorAll('.vx_steppedFlow-slide'),
			direction = currentStep < requestedStep ? 'right' : 'left',
			cachedSlideHeight;

		// Decrement the count so first step starts at 1 and not 0
		currentStep--;
		requestedStep--;

		function prepForSlide(startHeight) {
			// container.style.height = startHeight + 'px';
			container.classList.add('vx_prepForAnimation');
			animatingEl.classList.add('vx_slide-' + direction + '_start');
			animatingEl.focus();

			// add 'active' class to requested module, so both it and current module are active/visible before animating
			slides[requestedStep].classList.add('vx_activeSlide');

			animatingEl.classList.add('vx_prepToSlide');

			setTimeout(function () {

				animatingEl.classList.add('vx_slide-' + direction + '_end');

				// This code needs to be delayed to work properly
				setTimeout(function () {
					measureElHeight(slides[requestedStep], function (endHeight) {
						cachedSlideHeight = endHeight;
						// Wait to animate the height until the module completes sliding into position
						//container.style.height = endHeight + 'px';

						if (VX.featDetection.hasTransition) {
							animatingEl.addEventListener('transitionend', completeSlide, false);
						} else {
							setTimeout(completeSlide, 300);
						}
					});
				}, 50);
			}, 35);
		}
		function completeSlide() {
			var cntnrClassList = animatingEl.classList;

			cntnrClassList.remove(
				'vx_prepToSlide',
				'vx_slide-right_start',
				'vx_slide-right_end',
				'vx_slide-left_start',
				'vx_slide-left_end'
			);

			container.removeAttribute('style');
			container.classList.remove('vx_prepForAnimation');

			slides[currentStep].classList.remove('vx_activeSlide');
			animatingEl.removeEventListener('transitionend', completeSlide, false);
		}
		if (cachedSlideHeight) {
			prepForSlide(cachedSlideHeight);
		} else {
			measureElHeight(slides[currentStep], prepForSlide);
		}
	}

	if (!win.VX) {
		console.error('Error: the component `core.js` is required.');
	} else if (!win.VX.transitions) {
		win.VX.transitions = {};
	}

	VX.transitions.slideToStep = slideToStep;
}(window, document));