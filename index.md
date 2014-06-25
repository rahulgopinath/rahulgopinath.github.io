---
layout: page
title: Rahul Gopinath
tagline: .
---
<link rel="icon" type="image/x-icon" href="/favicon.ico">
{% include JB/setup %}

Rahul is a PhD candidate in *Software Testing*, specializing in *Mutation Analysis*. His interests include Programming Languages, Statistics, and Logic.

Supervisor: Dr. Carlos Jensen  
Research Team: HCI  


### Teaching Assistant

<ul class="posts">
  {% for post in site.posts %}
    {% assign mytags = post.tags | strip_html | strip_newlines %}
    {% if mytags contains 'ta' %}
    <li><span>{{ post.date | date_to_string }}</span> &raquo; <a href="{{ BASE_PATH }}{{ post.url }}">{{ post.title }}</a> {{ post.e }}</li>
    {% endif %}
  {% endfor %}
</ul>

### Instructor

<ul class="posts">
  {% for post in site.posts %}
    {% assign mytags = post.tags | strip_html | strip_newlines %}
    {% if mytags contains 'instructor' %}
    <li><span>{{ post.date | date_to_string }}</span> &raquo; <a href="{{ BASE_PATH }}{{ post.url }}">{{ post.title }}</a> {{ post.e }}</li>
    {% endif %}
  {% endfor %}
</ul>

