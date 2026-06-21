/* ═══════════════════════════════════════════════
   Common: nav scroll + mobile menu + scroll-top
   ═══════════════════════════════════════════════ */
(function () {
  var nav = document.getElementById("mainNav");
  var scrollBtn = document.getElementById("scrollTop");

  if (nav) {
    window.addEventListener("scroll", function () {
      nav.classList.toggle("scrolled", window.scrollY > 50);
      if (scrollBtn) {
        scrollBtn.classList.toggle("show", window.scrollY > 400);
      }
    });
  }

  if (scrollBtn) {
    scrollBtn.addEventListener("click", function () {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  var toggle = document.getElementById("navToggle");
  var links = document.getElementById("navLinks");
  if (toggle && links) {
    toggle.addEventListener("click", function () {
      links.classList.toggle("open");
    });
    var anchors = links.querySelectorAll("a");
    for (var i = 0; i < anchors.length; i++) {
      anchors[i].addEventListener("click", function () {
        links.classList.remove("open");
      });
    }
  }
})();


/* ═══════════════════════════════════════════════
   Ideas page: expandable cards
   ═══════════════════════════════════════════════ */
function initIdeas() {
  var grid = document.getElementById("ideasGrid");
  if (!grid || typeof IDEAS === "undefined") return;

  var zhNum = ["","一","二","三","四","五","六","七","八","九","十","十一","十二"];

  IDEAS.forEach(function (idea, i) {
    var card = document.createElement("div");
    card.className = "idea-card";

    var quotesHtml = idea.quotes.map(function (q) {
      return q.text + '<span class="src"> ——' + q.src + "</span>";
    }).join("<br><br>");

    card.innerHTML =
      '<div class="idea-header">' +
        '<div class="idea-number">' + (zhNum[i + 1] || i + 1) + "</div>" +
        '<div class="idea-header-text">' +
          '<div class="idea-name">' + idea.name + "</div>" +
          '<div class="idea-quote-preview">' + idea.preview + "</div>" +
        "</div>" +
        '<div class="idea-toggle">&#9662;</div>' +
      "</div>" +
      '<div class="idea-body">' +
        '<div class="idea-body-inner">' +
          '<div class="idea-full-quote">' + quotesHtml + "</div>" +
          '<div class="idea-explain">' + idea.explain + "</div>" +
          '<div class="idea-insight">' + idea.insight + "</div>" +
        "</div>" +
      "</div>";

    var header = card.querySelector(".idea-header");
    header.addEventListener("click", function () {
      var isOpen = card.classList.contains("open");
      card.classList.toggle("open", !isOpen);
    });

    grid.appendChild(card);
  });
}


/* ═══════════════════════════════════════════════
   Reader page: chapter navigation
   ═══════════════════════════════════════════════ */
function initReader() {
  var sidebar = document.getElementById("chapSidebar");
  var chapNum = document.getElementById("chapNum");
  var chapText = document.getElementById("chapText");
  var prevBtn = document.getElementById("prevBtn");
  var nextBtn = document.getElementById("nextBtn");

  if (!sidebar || typeof CHAPTERS === "undefined") return;

  var current = 0;
  var links = [];

  // Build sidebar
  var ul = document.createElement("ul");
  ul.className = "chap-list";

  for (var i = 0; i < CHAPTERS.length; i++) {
    (function (idx) {
      var li = document.createElement("li");
      var a = document.createElement("a");
      a.href = "#";
      a.textContent = "第" + (idx + 1) + "章";
      a.addEventListener("click", function (e) {
        e.preventDefault();
        showChapter(idx);
      });
      li.appendChild(a);
      ul.appendChild(li);
      links.push(a);
    })(i);
  }
  sidebar.appendChild(ul);

  // Navigation buttons
  if (prevBtn) {
    prevBtn.addEventListener("click", function () {
      if (current > 0) showChapter(current - 1);
    });
  }
  if (nextBtn) {
    nextBtn.addEventListener("click", function () {
      if (current < CHAPTERS.length - 1) showChapter(current + 1);
    });
  }

  function showChapter(idx) {
    current = idx;
    chapNum.textContent = "第" + (idx + 1) + "章";
    chapText.textContent = CHAPTERS[idx];

    if (prevBtn) prevBtn.disabled = idx === 0;
    if (nextBtn) nextBtn.disabled = idx === CHAPTERS.length - 1;

    for (var j = 0; j < links.length; j++) {
      links[j].classList.toggle("active", j === idx);
    }

    // Scroll the active sidebar link into view
    if (links[idx]) {
      links[idx].scrollIntoView({ block: "nearest", behavior: "smooth" });
    }
  }

  // Show first chapter
  showChapter(0);
}


/* ═══════════════════════════════════════════════
   Init on DOMContentLoaded
   ═══════════════════════════════════════════════ */
document.addEventListener("DOMContentLoaded", function () {
  initIdeas();
  initReader();
});
