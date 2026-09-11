// The body of each desktop window, held here so a route can ship only its
// own content and stay a distinct document for crawlers. The client pulls
// the others from /windows/<id>.html the first time one is opened.

export const WINDOW_HTML = {
  welcome: `              <div class="welcome">
                <img class="welcome-mark" src="/client-logo-dark.svg" alt="Alma" style="filter: invert(1) brightness(2);">
                <h1>An AI-native interface for your computer.</h1>
                <p>The computer interface has changed little since the GUI made apps, windows, and files the way we work.<span class="intro-followup">AI changes what computers can understand. The interface should begin with intent and context, not with apps and menus. Alma is a new interface for the computer that keeps you <span class="no-break">in control.</span></span></p>

                <form class="waitlist" action="/waitlist" method="post">
                  <label class="sr-only" for="page-email">Email address</label>
                  <input id="page-email" class="ph-no-autocapture" name="email" type="email" inputmode="email" enterkeyhint="go" placeholder="Enter email address" autocomplete="email" data-ph-no-autocapture required>
                  <button type="submit" disabled>Continue</button>
                  <p class="confirmation" role="status" aria-live="polite">You&rsquo;re on the waitlist</p>
                </form>

              </div>
            `,
  demos: `              <div class="finder-grid">
                <a href="/demos/blender/" class="finder-tile" data-open="blender">
                  <span class="tile-art">
                    <img src="/page/desktop/demos/blender-poster.jpg" alt="" loading="lazy">
                    <span class="tile-play"><svg viewBox="0 0 10 10" aria-hidden="true"><path d="M1 0.6l8 4.4-8 4.4z"/></svg></span>
                  </span>
                  <span class="tile-name">Blender demo</span>
                  <span class="tile-meta">Screen recording</span>
                </a>

                <a href="/demos/paint/" class="finder-tile" data-open="paint">
                  <span class="tile-art">
                    <img src="/page/desktop/demos/paint-poster.jpg" alt="" loading="lazy">
                    <span class="tile-play"><svg viewBox="0 0 10 10" aria-hidden="true"><path d="M1 0.6l8 4.4-8 4.4z"/></svg></span>
                  </span>
                  <span class="tile-name">Paint demo</span>
                  <span class="tile-meta">Screen recording</span>
                </a>
              </div>
            `,
  socials: `              <div class="finder-grid is-apps">
                <a class="finder-tile" href="https://x.com/alma_inc" target="_blank" rel="noopener noreferrer" data-platform="x">
                  <img class="tile-app" src="/page/desktop/icons/x.svg" alt="" width="192" height="192" loading="lazy">
                  <span class="tile-name">X</span>
                  <span class="tile-meta">@alma_inc</span>
                </a>
                <a class="finder-tile" href="https://www.instagram.com/thinkwithalma" target="_blank" rel="noopener noreferrer" data-platform="instagram">
                  <img class="tile-app" src="/page/desktop/icons/instagram.svg" alt="" width="192" height="192" loading="lazy">
                  <span class="tile-name">Instagram</span>
                  <span class="tile-meta">@thinkwithalma</span>
                </a>
                <a class="finder-tile" href="https://www.linkedin.com/company/tryalmanac/" target="_blank" rel="noopener noreferrer" data-platform="linkedin">
                  <img class="tile-app" src="/page/desktop/icons/linkedin.svg" alt="" width="192" height="192" loading="lazy">
                  <span class="tile-name">LinkedIn</span>
                  <span class="tile-meta">@tryalmanac</span>
                </a>
              </div>
            `,
  blender: `            <span class="caption-prompt">Build a rocket in Blender.</span>
            <span class="caption-note">Alma opens the app and models it with computer use. Under two minutes, about $0.30. Filmed off the screen, uncut.</span>
          `,
  paint: `            <span class="caption-prompt">Keep talking until there is a painting.</span>
            <span class="caption-note">Alma drives MS Paint by voice. The brush, the palette, the fill tool, the same surface a person would use.</span>
          `,
  manifesto: `              <article class="doc">
                <h1 class="doc-title">The computer should meet you where the work is.</h1>
                <p class="doc-lede">Software got a thousand times faster. The way we ask it for things did not. This is what we think the next interface has to be.</p>

                <h3><span class="doc-num">01</span> The interface stopped evolving.</h3>
                <p>Forty years ago the desktop metaphor was a breakthrough: files you could see, windows you could move, menus you could learn. Then it froze. We still open apps, hunt through menus, copy between windows, and keep the whole plan in our heads. Every year the machine gets better at thinking and we keep operating it by hand.</p>

                <h3><span class="doc-num">02</span> Intent is the primitive, not the app.</h3>
                <p>Apps organise software by vendor. Files organise work by storage. Neither is how anybody actually thinks. People think in outcomes: <em>finish the deck</em>, <em>answer the ones that matter</em>, <em>make this render</em>. An interface built on intent starts at the outcome and works out the apps for itself.</p>

                <h3><span class="doc-num">03</span> Context is not a feature. It is the whole thing.</h3>
                <p>An assistant that cannot see your screen, your files, and your last hour of work is a search box with better manners. Alma reads the room: what is open, what you just did, what this project is, what you meant last time. Without context there is no delegation, only dictation.</p>

                <h3><span class="doc-num">04</span> Work across what already exists.</h3>
                <p>We are not asking anyone to move house. The tools you use are the tools. Alma operates them the way you do, clicking, typing, navigating, waiting, so nothing has to be rewritten, integrated, or replaced before it can be automated. If a human can drive it, Alma can drive it.</p>

                <h3><span class="doc-num">05</span> You stay in control.</h3>
                <p>Autonomy without visibility is a bet, not a product. You watch the cursor move. You see each step as it happens. You can stop it, correct it, or take the keyboard back mid-task and finish it yourself. Trust is earned in public, one visible action at a time.</p>

                <h3><span class="doc-num">06</span> Show the real thing.</h3>
                <p>No demos that only run on the demo machine. The recordings in the Demos folder are unedited: a real Mac, real apps, real waiting. When something does not work yet, we would rather say so than stage it.</p>

                <div class="doc-signoff">
                  <p>If this is the problem you want to spend the next few years on, the door is open.</p>
                  <p><a href="/join-us/" class="doc-cta" data-open="joinus">Join us</a></p>
                </div>
              </article>
            `,
  joinus: `              <article class="doc">
                <h1 class="doc-title">People first. The role comes after.</h1>
                <p class="doc-lede">No specific roles are open right now. We are always open to hiring impressive people, and we work out where they fit afterwards.</p>
                <p>We do not index on resumes. If you are top 1% at whatever you do, get in touch.</p>
                <p>If you are interested in computer use, there is no other team you should be on.</p>
                <h3>Get in touch</h3>
                <p>Write a really short email. Attach one or two things you have built and are proud of, and tell us what intrigues you about Alma.</p>
                <p><a class="doc-cta" href="mailto:rkm@memfold.ai?subject=Alma" data-join-mail>rkm@memfold.ai</a></p>
              </article>
            `,
};
