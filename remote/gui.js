const _ = (x) => document.getElementById(x);
class GUI {
    static init() {
        GUI.setBposition();
        window.addEventListener('resize', GUI.setBposition);
        
        // add haptic feedback for all buttons and ensure the page is in fullscreen
        document.querySelectorAll('div.btn').forEach(div => {
            div.addEventListener('touchstart', event => {
                console.log(`div ${event.target.id} pressed`);
                event.target.classList.add('pressed');
                GUI.attemptFullscreen();
                GUI.hapticFeedback();
            });
            div.addEventListener('touchend', event => {
                console.log(`div ${event.target.id} released`);
                event.target.classList.remove('pressed');
                GUI.hapticFeedback();
            });
        });
    }
    static attemptFullscreen() {
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
    static hapticFeedback(n=50) {
        if (navigator.vibrate) {
            navigator.vibrate(n);
        }
    }
    static setBposition() {
        let dist = _('aBtn').getBoundingClientRect().top - 127.5;
        document.documentElement.style.setProperty('--bBtn-top', `${dist}px`);
    }
    static setSlot(s) {
        _('lights').children[s].classList.add('on');
    }
}

GUI.init();