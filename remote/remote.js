function attemptFullscreen() {
    return;
    let elem = document.documentElement;
    if (elem.requestFullscreen) {
        elem.requestFullscreen();
    } else if (elem.mozRequestFullScreen) {
        elem.mozRequestFullScreen();
    } else if (elem.webkitRequestFullscreen) {
        elem.webkitRequestFullscreen();
    } else if (elem.msRequestFullscreen) {
        elem.msRequestFullscreen();
    }

    // request wake lock too
    if (navigator.requestWakeLock) {
        navigator.wakeLock.request("screen");
    }
}

// add haptic feedback for all buttons and ensure the page is in fullscreen
document.querySelectorAll('div.btn').forEach(div => {
    div.addEventListener('touchstart', event => {
        console.log(`div ${event.target.id} pressed`);
        event.target.classList.add('pressed');
        attemptFullscreen();
        hapticFeedback();
    });
    div.addEventListener('touchend', event => {
        console.log(`div ${event.target.id} released`);
        event.target.classList.remove('pressed');
        hapticFeedback();
    });
});

// lock screen orientation to portrait
window.addEventListener("orientationchange", function(event) {
    if (screen.orientation.angle !== 0) {
        screen.orientation.lock("portrait");
    }
});

// haptic feedback
function hapticFeedback(n=50) {
    if (navigator.vibrate) {
        navigator.vibrate(n);
    }
}
