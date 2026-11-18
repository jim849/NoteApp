# Class 10 — Stored XSS (NotesApp flaw #10)

I checked how NotesApp displays grade comments. Once a teacher saves a comment, it appears on the student's dashboard and in the teacher's grade list. Both pages read and decrypt the stored comment before passing it to Jinja, so I checked the comment cell in each template.

## Before the fix

In commit `ba23165`, both `web/templates/dashboard.html` and `web/templates/teacher.html` wrapped `n.comment` in `{% autoescape false %}`. This let comment text go straight into the HTML response. Since the comment is stored in the database, the same content is rendered each time someone opens the relevant grade page.

I rendered both old templates with an ordinary comment containing `<`, `>` and `&`. Both templates produced the following HTML with those characters left unescaped.

```html
<td>Score < 10 on parts 1 & 2, aim for > 10 next time.</td>
```

## Fix

I removed the block that disabled autoescaping in both templates. The comment cell now uses a regular Jinja expression.

```html
<td>{{ n.comment }}</td>
```

Jinja now escapes special characters when it generates the HTML. This applies to both existing comments and newly submitted ones.

## Verification

I rendered both templates again with the same comment. In the generated HTML, `<`, `>` and `&` became `&lt;`, `&gt;` and `&amp;`, respectively. Decoding those entities gave me the original comment character for character.

```html
<td>Score &lt; 10 on parts 1 &amp; 2, aim for &gt; 10 next time.</td>
```

I also tried a comment containing an HTML tag. Both templates rendered `<em>Review</em>` as `&lt;em&gt;Review&lt;/em&gt;`, so the tag is visible as text in the comment cell.

I added both inputs to the regression tests. Each test checks the student and teacher templates, and **both tests passed**.

```sh
python3 -m unittest discover -s web/tests -p test_stored_xss.py -v
```
