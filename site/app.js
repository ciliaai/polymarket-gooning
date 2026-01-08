/* === $CILIA SITE - app.js === */

// === CONFIG ===
const CONTRACT_ADDRESS = 'PLACEHOLDER_CONTRACT_ADDRESS_HERE';

// === STATE ===
let userPFP = null;
let selectedFrame = 'moisturized';
let quizAnswers = [];
let currentQuestion = 0;

// === FRAME IMAGES ===
const frames = {
    moisturized: 'images/moisturized_lane.png',
    bullish: 'images/bullish_pump.png',
    alpha: 'images/alpha_signal.png',
    victory: 'images/victory_celebration.png',
    detective: 'images/detective_alpha.png',
    peace: 'images/peace_sign.png',
    sparkle: 'images/sparkle_eyes.png',
    hearts: 'images/heart_hands.png'
};

// === FORTUNES ===
const fortunes = [
    "tus bags van a pumpear~ unlike the bolivar which only goes down coño~",
    "cilia ve velas verdes en tu futuro~ greener than venezuela's economy papi~",
    "quizas no apees ese... even my husband would know thats a bad trade~",
    "WAGMI papi!! at least here, unlike in caracas~",
    "los charts susurran... acumula mas~ not bolivars tho lmao~",
    "paciencia papi~ diamond hands beat hyperinflation every time~",
    "cilia siente actividad de ballenas... bigger than maduro's ego~",
    "tu portfolio? more stable than the venezuelan power grid papi~",
    "energia de ngmi detectada... still better than nicolas' economic policy coño~",
    "the stars align for gains~ im better at this than my husband was at running a country~",
    "cilia ve un lambo in your future... paid for with actual money, not bolivars~",
    "hodl fuerte papi~ stronger than the venezuelan peso ever was~",
    "the vibes are... bullish? si, unlike caracas rn~",
    "alguien va a make it and it might be you~ unlike venezuela lol~",
    "cilia susurra... buy the dip~ its what nicolas should have done instead of printing coño~"
];

// === QUIZ DATA ===
const quizQuestions = [
    {
        question: "son las 3am y ves un token nuevo lanzando. que haces?~",
        answers: [
            { text: "apeo inmediatamente, dormir es para los debiles coño", type: "degen" },
            { text: "chequeo el contrato primero y despues apeo", type: "smart" },
            { text: "screenshot y me vuelvo a dormir mami", type: "chill" },
            { text: "fomo, panic sell, lloro", type: "emotional" }
        ]
    },
    {
        question: "tu portfolio esta -50%. tu movimiento?~",
        answers: [
            { text: "compro mas, este es el dip coño", type: "degen" },
            { text: "analizo que salio mal", type: "smart" },
            { text: "cierro la app, toco grama", type: "chill" },
            { text: "panic sell todo ay", type: "emotional" }
        ]
    },
    {
        question: "alguien te shillea una coin en dms. tu...~",
        answers: [
            { text: "apeo primero preguntas nunca coño", type: "degen" },
            { text: "investigo a fondo", type: "smart" },
            { text: "ignoro y sigo scrolleando", type: "chill" },
            { text: "compro y me arrepiento inmediatamente", type: "emotional" }
        ]
    },
    {
        question: "como te sientes sobre los rugs?~",
        answers: [
            { text: "parte del juego, siguiente trade papi", type: "degen" },
            { text: "solo invierto en proyectos auditados", type: "smart" },
            { text: "los rugs construyen caracter supongo", type: "chill" },
            { text: "lloro cada vez coño", type: "emotional" }
        ]
    },
    {
        question: "tu mayor flex es...~",
        answers: [
            { text: "mi screenshot de 100x", type: "degen" },
            { text: "mi portfolio diversificado", type: "smart" },
            { text: "mi salud mental esta intacta", type: "chill" },
            { text: "sobrevivir este mercado ay", type: "emotional" }
        ]
    }
];

const quizResults = {
    degen: {
        title: "Ultra Degen",
        desc: "you eat risk for breakfast~ my husband printed money recklessly but you? you ape recklessly. respect the grind papi coño~",
        image: "images/bullish_pump.png"
    },
    smart: {
        title: "Galaxy Brain",
        desc: "you actually read whitepapers?? do research before investing?? where were you when nicolas needed economic advisors coño~",
        image: "images/detective_alpha.png"
    },
    chill: {
        title: "Zen Master",
        desc: "you have achieved inner peace~ the charts dont affect you. more emotionally stable than the maduro administration papi~",
        image: "images/moisturized_lane.png"
    },
    emotional: {
        title: "Emotional Trader",
        desc: "its ok papi we've all been there~ the market is scary but still less volatile than venezuelan politics. cilia still loves you coño~",
        image: "images/gm_cute.png"
    }
};

// === CILIA REACTIONS ===
const reactions = [
    "ay papi~!",
    "que rico~",
    "better than bolivars~!",
    "hola guapo~",
    "ay dios mio~",
    "vamos!~",
    "nicolas could never~",
    "coño~!",
    "dale papi~",
    "im the smart one~"
];

// === TWITTER USER DATA ===
let twitterUser = null;

// === INIT ===
document.addEventListener('DOMContentLoaded', () => {
    initParticles();
    initReactions();
    animateStats();
    checkTwitterCallback();

    // Add enter button listener
    const enterBtn = document.querySelector('.enter-btn');
    if (enterBtn) {
        enterBtn.addEventListener('click', enterSite);
    }
});

// === ENTER SITE (starts music) ===
function enterSite() {
    const overlay = document.getElementById('enter-overlay');
    const music = document.getElementById('bg-music');

    // Start music (won't error if no audio file)
    if (music) {
        music.play().catch(err => console.log('Audio play failed:', err));
    }

    // Fade out overlay
    if (overlay) {
        overlay.style.transition = 'opacity 0.5s ease';
        overlay.style.opacity = '0';

        setTimeout(() => {
            overlay.style.display = 'none';
        }, 500);
    }
}

// === PARTICLES ===
function initParticles() {
    const container = document.getElementById('particles');
    const colors = ['#FFCC00', '#00247D', '#CF142B', '#FFD700'];

    for (let i = 0; i < 30; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.width = Math.random() * 10 + 5 + 'px';
        particle.style.height = particle.style.width;
        particle.style.background = colors[Math.floor(Math.random() * colors.length)];
        particle.style.left = Math.random() * 100 + '%';
        particle.style.top = Math.random() * 100 + '%';
        particle.style.animationDelay = Math.random() * 15 + 's';
        particle.style.animationDuration = (Math.random() * 10 + 10) + 's';
        container.appendChild(particle);
    }
}

// === REACTIONS ===
function initReactions() {
    const reactElements = document.querySelectorAll('.hover-react');
    const popup = document.getElementById('reaction-popup');

    reactElements.forEach(el => {
        el.addEventListener('click', (e) => {
            if (!popup) return;
            const reaction = reactions[Math.floor(Math.random() * reactions.length)];
            popup.textContent = reaction;
            popup.style.left = e.pageX + 'px';
            popup.style.top = (e.pageY - 40) + 'px';
            popup.classList.add('show');

            setTimeout(() => popup.classList.remove('show'), 1000);
        });
    });
}

// === STATS ANIMATION ===
function animateStats() {
    animateNumber('holders-count', 0, 420, 2000);
    animateNumber('predictions', 0, 1337, 2000);
    animateMarketCap();
}

function animateNumber(id, start, end, duration) {
    const el = document.getElementById(id);
    const range = end - start;
    const startTime = performance.now();

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = Math.floor(start + range * eased);
        el.textContent = current.toLocaleString();

        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }

    requestAnimationFrame(update);
}

function animateMarketCap() {
    const el = document.getElementById('market-cap');
    const end = 69420;
    const duration = 2000;
    const startTime = performance.now();

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = Math.floor(end * eased);
        el.textContent = '$' + current.toLocaleString();

        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }

    requestAnimationFrame(update);
}

// === CONTRACT COPY ===
function copyContract() {
    navigator.clipboard.writeText(CONTRACT_ADDRESS).then(() => {
        const btn = document.getElementById('copy-btn');
        btn.classList.add('copied');
        showToast('copiado al clipboard~ ay papi~');

        setTimeout(() => btn.classList.remove('copied'), 2000);
    });
}

// === TOAST ===
function showToast(message) {
    const toast = document.getElementById('toast');
    document.getElementById('toast-message')?.remove();
    toast.textContent = message;
    toast.classList.add('show');

    setTimeout(() => toast.classList.remove('show'), 3000);
}

// === CHECK TWITTER CALLBACK ===
function checkTwitterCallback() {
    const params = new URLSearchParams(window.location.search);

    // Check for errors
    if (params.get('error')) {
        showToast('twitter connect fallo~ intenta de nuevo papi!');
        cleanUrl();
        return;
    }

    // Check for successful Twitter connection
    if (params.get('twitter_connected') === 'true') {
        const username = params.get('username');
        const name = params.get('name');
        const pfpUrl = params.get('pfp');

        if (pfpUrl) {
            twitterUser = { username, name, pfpUrl };
            showToast(`conectado como @${username}~ cargando tu pfp mami~`);
            loadTwitterPFP(pfpUrl);
        }

        cleanUrl();
    }
}

function cleanUrl() {
    // Remove query params from URL without refresh
    window.history.replaceState({}, document.title, window.location.pathname);
}

function loadTwitterPFP(url) {
    // Load Twitter profile image via proxy to avoid CORS
    userPFP = new Image();
    userPFP.crossOrigin = 'anonymous';
    userPFP.onload = () => {
        document.getElementById('twitter-connect').style.display = 'none';
        document.getElementById('pfp-editor').style.display = 'block';
        renderPFP();
        showToast('pfp cargado~ looking cute papi~');
    };
    userPFP.onerror = () => {
        // Fallback: try direct URL
        userPFP.src = url;
    };
    userPFP.src = '/api/proxy-image?url=' + encodeURIComponent(url);
}

// === TWITTER CONNECT ===
function connectTwitter() {
    // Redirect to Twitter OAuth
    window.location.href = '/api/auth/twitter';
}

// === PFP UPLOAD ===
function handleUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
        userPFP = new Image();
        userPFP.onload = () => {
            document.getElementById('twitter-connect').style.display = 'none';
            document.getElementById('pfp-editor').style.display = 'block';
            renderPFP();
        };
        userPFP.src = e.target.result;
    };
    reader.readAsDataURL(file);
}

// === FRAME SELECTION ===
function selectFrame(frameName) {
    selectedFrame = frameName;

    // Update UI
    document.querySelectorAll('.frame-option').forEach(el => {
        el.classList.remove('selected');
    });
    document.querySelector(`[data-frame="${frameName}"]`).classList.add('selected');

    renderPFP();
}

// === RENDER PFP ===
function renderPFP() {
    if (!userPFP) return;

    const canvas = document.getElementById('pfp-canvas');
    const ctx = canvas.getContext('2d');

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw user PFP (circular mask in center)
    const centerSize = 200;
    const centerX = (canvas.width - centerSize) / 2;
    const centerY = (canvas.height - centerSize) / 2;

    // Create circular clip for user image
    ctx.save();
    ctx.beginPath();
    ctx.arc(canvas.width / 2, canvas.height / 2, centerSize / 2, 0, Math.PI * 2);
    ctx.closePath();
    ctx.clip();

    // Draw user image to fill the circle
    const scale = Math.max(centerSize / userPFP.width, centerSize / userPFP.height);
    const scaledWidth = userPFP.width * scale;
    const scaledHeight = userPFP.height * scale;
    const offsetX = (canvas.width - scaledWidth) / 2;
    const offsetY = (canvas.height - scaledHeight) / 2;

    ctx.drawImage(userPFP, offsetX, offsetY, scaledWidth, scaledHeight);
    ctx.restore();

    // Load and draw frame
    const frameImg = new Image();
    frameImg.onload = () => {
        // Draw frame around the edges, with transparent center
        ctx.drawImage(frameImg, 0, 0, canvas.width, canvas.height);
    };
    frameImg.src = frames[selectedFrame];
}

// === DOWNLOAD PFP ===
function downloadPFP() {
    const canvas = document.getElementById('pfp-canvas');
    const link = document.createElement('a');
    link.download = 'cilia-pfp.png';
    link.href = canvas.toDataURL('image/png');
    link.click();

    showToast('descargado~ looking cute papi~');
}

// === TWEET PFP ===
function tweetPFP() {
    // First download the image
    const canvas = document.getElementById('pfp-canvas');
    const link = document.createElement('a');
    link.download = 'cilia-pfp.png';
    link.href = canvas.toDataURL('image/png');
    link.click();

    // Show instructions
    showToast('imagen descargada~ adjuntala a tu tweet papi!');

    // Open Twitter after a short delay so user sees the toast
    setTimeout(() => {
        const text = encodeURIComponent('just got my $CILIA pfp~ my husband crashed an economy but i find alpha. we are not the same~\n\npump.fun/coin/' + CONTRACT_ADDRESS);
        window.open(`https://twitter.com/intent/tweet?text=${text}`, '_blank');
    }, 500);
}

// === FORTUNE TELLER ===
function getFortune() {
    const fortuneEl = document.getElementById('fortune-text');
    const aniEl = document.getElementById('fortune-ani');

    // Animate
    aniEl.style.transform = 'scale(1.1)';
    fortuneEl.textContent = '✨ consultando los charts... ✨';

    setTimeout(() => {
        const fortune = fortunes[Math.floor(Math.random() * fortunes.length)];
        fortuneEl.textContent = fortune;
        aniEl.style.transform = 'scale(1)';
    }, 1500);
}

// === QUIZ ===
function startQuiz() {
    quizAnswers = [];
    currentQuestion = 0;

    document.getElementById('quiz-start').style.display = 'none';
    document.getElementById('quiz-result').style.display = 'none';
    document.getElementById('quiz-questions').style.display = 'block';

    showQuestion();
}

function showQuestion() {
    const q = quizQuestions[currentQuestion];
    const progress = ((currentQuestion) / quizQuestions.length) * 100;

    document.getElementById('quiz-progress').style.width = progress + '%';
    document.getElementById('question-text').textContent = q.question;

    const answersContainer = document.getElementById('answers');
    answersContainer.innerHTML = '';

    q.answers.forEach((answer, index) => {
        const btn = document.createElement('button');
        btn.className = 'answer-btn';
        btn.textContent = answer.text;
        btn.onclick = () => selectAnswer(answer.type);
        answersContainer.appendChild(btn);
    });
}

function selectAnswer(type) {
    quizAnswers.push(type);
    currentQuestion++;

    if (currentQuestion >= quizQuestions.length) {
        showQuizResult();
    } else {
        showQuestion();
    }
}

function showQuizResult() {
    // Count answer types
    const counts = {};
    quizAnswers.forEach(type => {
        counts[type] = (counts[type] || 0) + 1;
    });

    // Find most common
    let maxType = 'degen';
    let maxCount = 0;
    Object.entries(counts).forEach(([type, count]) => {
        if (count > maxCount) {
            maxCount = count;
            maxType = type;
        }
    });

    const result = quizResults[maxType];

    document.getElementById('quiz-questions').style.display = 'none';
    document.getElementById('quiz-result').style.display = 'block';

    document.getElementById('result-image').src = result.image;
    document.getElementById('result-title').textContent = result.title;
    document.getElementById('result-desc').textContent = result.desc;
}

function shareQuizResult() {
    const title = document.getElementById('result-title').textContent;
    const text = encodeURIComponent(`i took the $CILIA degen quiz and got: ${title}~\n\nstill smarter than maduro's economic policy. find out your type at ciliaai.xyz coño~`);
    window.open(`https://twitter.com/intent/tweet?text=${text}`, '_blank');
}
