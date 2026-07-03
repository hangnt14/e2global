/**
 * dom-extractor.js
 * Extracts structured BA-relevant DOM information from a Playwright page.
 * Runs page.evaluate() to capture forms, buttons, links, headings, tables.
 */

/**
 * Extract structured DOM data from the current page.
 * @param {import('playwright').Page} page
 * @returns {Promise<object>} structured DOM snapshot
 */
export async function extractDOM(page) {
  return page.evaluate(() => {
    // Forms
    const forms = Array.from(document.querySelectorAll('form')).map((form) => ({
      action: form.action || form.getAttribute('action') || '',
      method: (form.method || 'get').toUpperCase(),
      inputs: Array.from(form.querySelectorAll('input, select, textarea')).map((el) => ({
        name: el.name || el.id || '',
        type: el.type || el.tagName.toLowerCase(),
        required: el.required || false,
        placeholder: el.placeholder || '',
        label: (() => {
          const label = el.id
            ? document.querySelector(`label[for="${el.id}"]`)
            : el.closest('label');
          return label ? label.textContent.trim() : '';
        })(),
      })).filter((i) => i.name || i.placeholder),
    }));

    // Buttons
    const buttons = Array.from(
      document.querySelectorAll('button, input[type="submit"], input[type="button"]')
    ).map((el) => ({
      text: (el.textContent || el.value || '').trim(),
      type: el.type || 'button',
    })).filter((b) => b.text);

    // Links (same-origin only for navigation mapping)
    const links = Array.from(document.querySelectorAll('a[href]'))
      .map((a) => ({
        text: a.textContent.trim(),
        href: a.href,
      }))
      .filter((l) => l.href && !l.href.startsWith('mailto:') && !l.href.startsWith('tel:'));

    // Headings
    const headings = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6')).map(
      (h) => ({
        level: parseInt(h.tagName[1]),
        text: h.textContent.trim(),
      })
    ).filter((h) => h.text);

    // Tables (column headers only)
    const tables = Array.from(document.querySelectorAll('table')).map((table) => ({
      headers: Array.from(table.querySelectorAll('th')).map((th) => th.textContent.trim()),
      rowCount: table.querySelectorAll('tr').length,
    })).filter((t) => t.headers.length > 0);

    // Navigation menus
    const navItems = Array.from(document.querySelectorAll('nav a, [role="navigation"] a'))
      .map((a) => ({ text: a.textContent.trim(), href: a.href }))
      .filter((n) => n.text && n.href);

    return {
      title: document.title,
      metaDescription:
        document.querySelector('meta[name="description"]')?.getAttribute('content') || '',
      url: window.location.href,
      forms,
      buttons,
      links,
      headings,
      tables,
      navItems,
    };
  });
}
