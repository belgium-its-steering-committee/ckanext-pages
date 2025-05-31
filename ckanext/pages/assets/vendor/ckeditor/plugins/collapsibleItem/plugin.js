"use strict";

const TITLE_CLASS = "collapsible-item-heading";
const BODY_CLASS = "collapsible-item-body";
const TITLE_ALLOWED_CONTENT =
  "span[style]{*};h1[style]{*};h2[style]{*};h3[style]{*};h4[style]{*}; strong[syle]{*}; em[style]{*}; u[style]{*};a(*)[*];";
const BODY_ALLOWED_CONTENT =
  "p[style]{*};h1[style]{*};h2[style]{*};h3[style]{*};h4[style]{*};br[style]{*};span[style]{*};ul[style]{*};ol[style]{*};li[style]{*};strong[style]{*};b[style]{*};em[style]{*};u[style]{*};table[style]{*};tbody[style]{*};thead[style]{*};tr[style]{*};td[style]{*};th[style]{*};hr[style]{*};a;a[style]{*};a(*)[*];img(*)[*];";
const ALLOWED_CONTENT =
  "div(!collapsible-item*,panel*,collapse)[*];h4(!collapsible-item*,panel*)[*];a(!collapsible-item*,collapsed,panel*)[*];span(*)[*];*{color};*{border};*{background-color}";
const TITLE_SPAN_CLASS = "collapsible-item-title-link-text";

/**
 * This is only used the first time the widget is inserted
 * After page save and reload the html from upcast/downcast will be used
 */
function getCollapsibleItemInit() {
  return /* html */ `<div class="collapsible-item">
    <h2 class="${TITLE_CLASS}">
      <div class="collapsible-item-title-link">
        <span class="${TITLE_SPAN_CLASS}">
          Title Text
        </span>
      </div>
    </h2>
    <div class="${BODY_CLASS}">
      Body Text
    </div>
</div>`;
}

function getCollapsibleElement(titleHtml, contentHtml) {
  const uniqueId = `collapsible_${Date.now()}_${Math.floor(
    Math.random() * 9999999
  )}`;
  return CKEDITOR.htmlParser.fragment.fromHtml(/* html */ `
          <div class="accordion-item collapsible-item">
            <h2
              class="accordion-header ${TITLE_CLASS}"
              id="heading-for-${uniqueId}"
            >
              <button
                class="accordion-button collapsed collapsible-item-title-link"
                type="button"
                data-bs-toggle="collapse"
                data-bs-target="#${uniqueId}"
                aria-expanded="false"
                aria-controls="${uniqueId}"
              >
                <span class="${TITLE_SPAN_CLASS}">${titleHtml}</span>
              </button>
            </h2>
            <div
              id="${uniqueId}"
              class="accordion-collapse collapse collapsible-item-collapse"
              aria-labelledby="heading${uniqueId}"
            >
              <div class="accordion-body ${BODY_CLASS}">
                ${contentHtml}
              </div>
            </div>
          </div>
        `).children[0];
}

function getNodeContent(node) {
  if (node.type === CKEDITOR.NODE_TEXT) {
    return node.value;
  } else if (node.type === CKEDITOR.NODE_ELEMENT) {
    return node.getHtml();
  }
}

CKEDITOR.plugins.add("collapsibleItem", {
  requires: "widget",
  icons: "collapsibleitem",
  hidpi: true,
  init: function (editor) {
    editor.widgets.add("collapsibleItem", {
      button: "Insert Collapsible Item",
      template: getCollapsibleItemInit(),
      editables: {
        title: {
          selector: `.${TITLE_CLASS}`,
          allowedContent: TITLE_ALLOWED_CONTENT,
        },
        body: {
          selector: `.${BODY_CLASS}`,
          allowedContent: BODY_ALLOWED_CONTENT,
        },
      },
      allowedContent: ALLOWED_CONTENT,
      requiredContent: "div(collapsible-item);",
      /**
       * TODO: ideally we would be able to return a completely different html on upcast
       * but ckeditor seems to break if we do this. Instead we just remove the classes
       * that make it collapse
       */
      upcast: function (element) {
        if (element.name == "div" && element.hasClass("collapsible-item")) {
          // Some manual parsing, not ideal but works for now
          const h2 = element.children[0];
          h2.removeClass("accordion-header");
          const button = h2.children[0];
          [
            "accordion-button",
            "collapsed",
            "collapsible-item-title-link",
          ].forEach((className) => {
            button.removeClass(className);
          });

          const bodyWrapper = element.children[1];
          [
            "accordion-collapse",
            "collapse",
            "collapsible-item-collapse",
          ].forEach((className) => {
            bodyWrapper.removeClass(className);
          });

          return element;
        }
      },
      downcast: function (withElement) {
        // Do manual parsing because we can't search for classes
        const titleHtml = getNodeContent(withElement.children[0].children[0]);
        const bodyHtml = getNodeContent(withElement.children[1].children[0]);

        return getCollapsibleElement(titleHtml, bodyHtml);
      },
    });
  },

  onLoad: function () {
    CKEDITOR.addCss(
      "a.collapsible-item-title-link { display: block; }" +
        '.collapsible-item::before {font-size:10px;color:#000;content: "collapsible element"}' +
        ".collapsible-item-heading {background-color:white;text-decoration:none;font-size:16px;border-radius:5px;padding:0.5rem} " +
        ".collapsible-item-collapse {display:block;background-color:#ddd;min-height:10px;} " +
        ".collapsible-item {padding: 8px;margin: 10px;background: #eee;border-radius: 8px;border: 1px solid #ddd;box-shadow: 0 1px 1px #fff inset, 0 -1px 0px #ccc inset;}" +
        ".collapsible-item-title, .collapsible-item-body {box-shadow: 0 1px 1px #ddd inset;border: 1px solid #cccccc;border-radius: 5px;background: #fff;}" +
        ".collapsible-item-title {margin: 0 0 8px;padding: 5px 8px;}" +
        ".collapsible-item-body {padding: 0 8px;}" +
        ".collapsible-item-title-link-text {min-width:50px;display:inline-block;min-height:20px;height:100%;}" +
        ".collapsible-item-title-link-icon {display:inline-block;float:right;}"
    );
  },
});
