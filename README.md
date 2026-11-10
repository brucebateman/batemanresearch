# Bateman Research website

Modernized, single-page static rebuild of [batemanresearch.com](https://www.batemanresearch.com), replacing the GoDaddy Website Builder version (content taken from the last archived copy, January 2026).

## What changed

- One fast static page (`index.html`): no site builder, no tracking, no cookie banner.
- Clearer copy: hero, services, coverage (topics and regions), how we work, speaking, contact.
- "Research horizon" graphic that labels the 3 to 5 year window from the current year automatically.
- Light and dark mode, mobile menu, keyboard focus states, reduced-motion support.
- SEO: meta description, Open Graph tags and `ProfessionalService` structured data.
- Footer copyright year updates itself.

## Contact form

The form is not connected to a mail service yet. To deliver enquiries, create a form endpoint
(for example at Formspree) and set it on the form:

```html
<form id="contact-form" novalidate data-endpoint="https://formspree.io/f/your-id">
```

## Hosting

Any static host works. For GitHub Pages: Settings → Pages → deploy from `main`, root folder.
To serve it at www.batemanresearch.com, add a `CNAME` file containing the domain and point DNS at GitHub Pages.
