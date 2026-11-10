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

Enquiries are emailed to **info@batemanresearch.com** through [FormSubmit](https://formsubmit.co) (free, no account).
The form posts to `https://formsubmit.co/ajax/info@batemanresearch.com`, includes a hidden spam trap,
and sets the visitor's email as the reply-to address.

**One-time activation:** the first submission sends a confirmation email to info@batemanresearch.com.
Click the link in it, and later enquiries are delivered. That email also gives you a random alias;
to keep the address out of the page source, replace the email in the form's `data-endpoint` with the alias.

## Hosting

Any static host works. For GitHub Pages: Settings → Pages → deploy from `main`, root folder.
To serve it at www.batemanresearch.com, add a `CNAME` file containing the domain and point DNS at GitHub Pages.
