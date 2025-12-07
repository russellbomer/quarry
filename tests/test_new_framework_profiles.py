"""Tests for new framework profiles (Django, Next.js, React, Vue.js)."""

from bs4 import BeautifulSoup

from quarry.framework_profiles import (
    DjangoAdminProfile,
    NextJSProfile,
    ReactComponentProfile,
    VueJSProfile,
    detect_framework,
)
from quarry.inspector import find_item_selector


def test_django_admin_detection():
    """Test that Django Admin interface is detected."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Django Administration</title>
        <link rel="stylesheet" href="/static/admin/css/base.css">
    </head>
    <body class="django-admin">
        <div id="content">
            <table>
                <thead>
                    <tr>
                        <th>Title</th>
                        <th>Author</th>
                        <th>Date</th>
                    </tr>
                </thead>
                <tbody>
                    <tr class="row1">
                        <th class="field-__str__"><a href="/admin/blog/post/1/">First Post</a></th>
                        <td class="field-author">John Doe</td>
                        <td class="field-created">2025-01-15</td>
                    </tr>
                    <tr class="row2">
                        <th class="field-__str__"><a href="/admin/blog/post/2/">Second Post</a></th>
                        <td class="field-author">Jane Smith</td>
                        <td class="field-created">2025-01-14</td>
                    </tr>
                    <tr class="row1">
                        <th class="field-__str__"><a href="/admin/blog/post/3/">Third Post</a></th>
                        <td class="field-author">Bob Johnson</td>
                        <td class="field-created">2025-01-13</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """

    # Test detection
    framework = detect_framework(html)
    assert framework is not None, "Should detect Django Admin"
    assert framework == DjangoAdminProfile, f"Expected DjangoAdminProfile, got {framework}"

    # Test selector hints
    results = find_item_selector(html)
    assert len(results) > 0, "Should find item selectors"

    # Check that table rows are detected
    tr_found = any("tr" in r["selector"] or "row" in r["selector"] for r in results)
    assert tr_found, "Should find table row selectors"


def test_nextjs_detection():
    """Test that Next.js applications are detected."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <script id="__NEXT_DATA__" type="application/json">
        {"props":{"pageProps":{}},"page":"/","query":{}}
        </script>
    </head>
    <body>
        <div id="__next">
            <div class="container">
                <article class="post-card">
                    <h2 class="post-title"><a href="/posts/first">First Post</a></h2>
                    <time datetime="2025-01-15">January 15, 2025</time>
                    <p class="post-excerpt">This is the first post</p>
                </article>
                <article class="post-card">
                    <h2 class="post-title"><a href="/posts/second">Second Post</a></h2>
                    <time datetime="2025-01-14">January 14, 2025</time>
                    <p class="post-excerpt">This is the second post</p>
                </article>
                <article class="post-card">
                    <h2 class="post-title"><a href="/posts/third">Third Post</a></h2>
                    <time datetime="2025-01-13">January 13, 2025</time>
                    <p class="post-excerpt">This is the third post</p>
                </article>
            </div>
        </div>
        <script src="/_next/static/chunks/main.js"></script>
    </body>
    </html>
    """

    # Test detection
    framework = detect_framework(html)
    assert framework is not None, "Should detect Next.js"
    assert framework == NextJSProfile, f"Expected NextJSProfile, got {framework}"

    # Test selector hints
    results = find_item_selector(html)
    assert len(results) > 0, "Should find item selectors"

    # Check that articles are detected
    article_found = any("article" in r["selector"] or "card" in r["selector"] for r in results)
    assert article_found, "Should find article/card selectors"


def test_react_detection():
    """Test that React applications are detected."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>React App</title>
    </head>
    <body>
        <div id="root" data-reactroot="">
            <div class="App">
                <div class="PostCard">
                    <h2 class="PostTitle">First Post</h2>
                    <a href="/posts/1" class="PostLink">Read more</a>
                    <time datetime="2025-01-15" class="PostDate">Jan 15</time>
                </div>
                <div class="PostCard">
                    <h2 class="PostTitle">Second Post</h2>
                    <a href="/posts/2" class="PostLink">Read more</a>
                    <time datetime="2025-01-14" class="PostDate">Jan 14</time>
                </div>
                <div class="PostCard">
                    <h2 class="PostTitle">Third Post</h2>
                    <a href="/posts/3" class="PostLink">Read more</a>
                    <time datetime="2025-01-13" class="PostDate">Jan 13</time>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    # Test detection
    framework = detect_framework(html)
    assert framework is not None, "Should detect React"
    assert framework == ReactComponentProfile, f"Expected ReactComponentProfile, got {framework}"

    # Test selector hints
    results = find_item_selector(html)
    assert len(results) > 0, "Should find item selectors"

    # Check that PostCard is detected
    card_found = any("Card" in r["selector"] or "PostCard" in r["selector"] for r in results)
    assert card_found, "Should find PostCard selectors"


def test_vuejs_detection():
    """Test that Vue.js applications are detected."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Vue App</title>
    </head>
    <body>
        <div id="app">
            <div class="posts">
                <article v-for="post in posts" :key="post.id" class="post-item">
                    <h2 class="post-title">First Post</h2>
                    <a href="/posts/1" class="post-link">Read more</a>
                    <time class="post-date">2025-01-15</time>
                </article>
                <article v-for="post in posts" :key="post.id" class="post-item">
                    <h2 class="post-title">Second Post</h2>
                    <a href="/posts/2" class="post-link">Read more</a>
                    <time class="post-date">2025-01-14</time>
                </article>
                <article v-for="post in posts" :key="post.id" class="post-item">
                    <h2 class="post-title">Third Post</h2>
                    <a href="/posts/3" class="post-link">Read more</a>
                    <time class="post-date">2025-01-13</time>
                </article>
            </div>
        </div>
        <script>
        new Vue({
            el: '#app',
            data: {
                posts: [
                    {id: 1, title: 'First Post', url: '/posts/1', date: '2025-01-15'},
                    {id: 2, title: 'Second Post', url: '/posts/2', date: '2025-01-14'},
                    {id: 3, title: 'Third Post', url: '/posts/3', date: '2025-01-13'}
                ]
            }
        });
        </script>
    </body>
    </html>
    """

    # Test detection
    framework = detect_framework(html)
    assert framework is not None, "Should detect Vue.js"
    assert framework == VueJSProfile, f"Expected VueJSProfile, got {framework}"

    # Test selector hints
    results = find_item_selector(html)
    assert len(results) > 0, "Should find item selectors"

    # Check that articles are detected
    article_found = any("article" in r["selector"] or "item" in r["selector"] for r in results)
    assert article_found, "Should find article/item selectors"


def test_django_field_mappings():
    """Test Django Admin field selector generation."""
    html = """
    <tr class="row1">
        <th class="field-__str__"><a href="/admin/blog/post/1/">Test Post</a></th>
        <td class="field-author">John Doe</td>
        <td class="field-created">2025-01-15</td>
    </tr>
    """

    soup = BeautifulSoup(html, "html.parser")
    row = soup.find("tr")

    # Test title field
    title_selector = DjangoAdminProfile.generate_field_selector(row, "title")
    assert title_selector is not None, "Should find title selector"
    assert "field-__str__" in title_selector or "field-title" in title_selector

    # Test author field
    author_selector = DjangoAdminProfile.generate_field_selector(row, "author")
    assert author_selector is not None, "Should find author selector"
    assert "field-author" in author_selector

    # Test date field
    date_selector = DjangoAdminProfile.generate_field_selector(row, "date")
    assert date_selector is not None, "Should find date selector"
    assert "field-created" in date_selector or "field-date" in date_selector


def test_nextjs_field_mappings():
    """Test Next.js field selector generation."""
    html = """
    <article class="post-card">
        <h2 class="post-title"><a href="/posts/first">First Post</a></h2>
        <time datetime="2025-01-15">January 15, 2025</time>
        <p class="post-excerpt">This is the first post</p>
    </article>
    """

    soup = BeautifulSoup(html, "html.parser")
    article = soup.find("article")

    # Test title field
    title_selector = NextJSProfile.generate_field_selector(article, "title")
    assert title_selector is not None, "Should find title selector"

    # Test date field
    date_selector = NextJSProfile.generate_field_selector(article, "date")
    assert date_selector is not None, "Should find date selector"
    assert "time" in date_selector or "date" in date_selector


def test_react_field_mappings():
    """Test React component field selector generation."""
    html = """
    <div class="PostCard">
        <h2 class="PostTitle">First Post</h2>
        <a href="/posts/1" class="PostLink">Read more</a>
        <time datetime="2025-01-15" class="PostDate">Jan 15</time>
        <p class="PostDescription">Post description here</p>
    </div>
    """

    soup = BeautifulSoup(html, "html.parser")
    card = soup.find("div", class_="PostCard")

    # Test title field
    title_selector = ReactComponentProfile.generate_field_selector(card, "title")
    assert title_selector is not None, "Should find title selector"
    assert "Title" in title_selector or "h2" in title_selector

    # Test description field
    desc_selector = ReactComponentProfile.generate_field_selector(card, "description")
    assert desc_selector is not None, "Should find description selector"


def test_framework_priority_order():
    """Test that more specific frameworks are detected before generic ones."""
    # Django Admin should be detected before generic patterns
    django_html = '<body class="django-admin"><div>Content</div></body>'
    framework = detect_framework(django_html)
    assert framework == DjangoAdminProfile, "Django should be detected"

    # Next.js should be detected
    nextjs_html = '<script id="__NEXT_DATA__"></script><div id="__next"></div>'
    framework = detect_framework(nextjs_html)
    assert framework == NextJSProfile, "Next.js should be detected"

    # React should be detected
    react_html = '<div id="root" data-reactroot=""></div>'
    framework = detect_framework(react_html)
    assert framework == ReactComponentProfile, "React should be detected"

    # Vue should be detected
    vue_html = '<div v-for="item in items"></div>'
    framework = detect_framework(vue_html)
    assert framework == VueJSProfile, "Vue.js should be detected"
