---
layout: page
title : Posts
header : Posts
group: navigation
weight: 3
menu: Posts
---


<h3> Writing a language </h3>

This was the teaching materials I prepared for a course in programming languages for which I was the instructor. These are still under construction since the classes typically had to refer back to previous sessions, and hence each post is a super set of the previous. (You will get most by just looking at the 7th installment)

<div class="posts">
  <ul>
  {% for post in site.posts reversed %}
  {% capture mytags%}{{ post.tags | first | split:" " | first }}{% endcapture %}
  {% if mytags == 'blog' %}
  <li><span>{{ post.date | date_to_string }}</span> &raquo; <a href="{{ BASE_PATH }}{{ post.url  }}">{{ post.title }}</a> {{ post.e }}</li>
  {% endif %}
  {% endfor %}
  </ul>
</div-->
