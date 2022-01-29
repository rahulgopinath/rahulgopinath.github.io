---
layout: page
title : Publications
header : Publications
group: navigation
weight: 6
menu: Publications
---
{% assign publications = site.posts | where_exp: "post","post.tags contains 'publication'" %}

<h3>Peer Reviewed Publications</h3>
{% assign peerreviewed = publications | where_exp: "post","post.thesort contains 'peerreviewed'" %}
{% assign pubsperYear = peerreviewed | group_by_exp:"post", "post.date | date: '%Y'" %}
<div class="posts">
{% for year in pubsperYear %}
<h5 id="{{year.name}}">{{ year.name }}</h5>
  <ul>
  {% for post in year.items%}
  {% assign authors = post.authors | split:"," %}
  {% capture myauthors %}{% for author in authors%}{% if author contains 'Rahul Gopinath' %}<b>Rahul Gopinath</b>{% else %}{{author}}{% endif %}{% if forloop.last == true %}{% else %}, {% endif %}{% endfor %}{% endcapture %}
  <li><a href="{{ BASE_PATH }}{{ post.url  }}">{{ post.title }}</a><br/>
  {{ myauthors}} <br/>
  {{ post.venue }} {{ post.date | date: "%Y"}}.</li>
  {% endfor %}
  </ul>
{% endfor %}
</div>

<h3>Technical Reports</h3>
{% assign techreports = publications | where_exp: "post","post.thesort contains 'techreport'" %}
{% assign pubsperYear = techreports | group_by_exp:"post", "post.date | date: '%Y'" %}
<div class="posts">
{% for year in pubsperYear %}
<h5 id="{{year.name}}">{{ year.name }}</h5>
  <ul>
  {% for post in year.items%}
  {% assign authors = post.authors | split:"," %}
  {% capture myauthors %}{% for author in authors%}{% if author contains 'Rahul Gopinath' %}<b>Rahul Gopinath</b>{% else %}{{author}}{% endif %}{% if forloop.last == true %}{% else %}, {% endif %}{% endfor %}{% endcapture %}
  <li><a href="{{ BASE_PATH }}{{ post.url  }}">{{ post.title }}</a><br/>
  {{ myauthors}} <br/>
  {{ post.venue }} {{ post.date | date: "%Y"}}.</li>
  {% endfor %}
  </ul>
{% endfor %}
</div>


<h3>Books</h3>
{% assign books = publications | where_exp: "post","post.thesort contains 'book'" %}
{% assign pubsperYear = books | group_by_exp:"post", "post.date | date: '%Y'" %}

<div class="posts">
{% for year in pubsperYear %}
<h5 id="{{year.name}}">{{ year.name }}</h5>
  <ul>
  {% for post in year.items%}
  {% assign authors = post.authors | split:"," %}
  {% capture myauthors %}{% for author in authors%}{% if author contains 'Rahul Gopinath' %}<b>Rahul Gopinath</b>{% else %}{{author}}{% endif %}{% if forloop.last == true %}{% else %}, {% endif %}{% endfor %}{% endcapture %}
  <li><a href="{{ BASE_PATH }}{{ post.url  }}">{{ post.title }}</a><br/>
  {{ myauthors}} <br/>
  {{ post.venue }} {{ post.date | date: "%Y"}}.</li>
  {% endfor %}
  </ul>
{% endfor %}
</div>


<h3>Thesis</h3>
{% assign thesis = publications | where_exp: "post","post.thesort contains 'thesis'" %}
{% assign pubsperYear = thesis | group_by_exp:"post", "post.date | date: '%Y'" %}

<div class="posts">
{% for year in pubsperYear %}
<h5 id="{{year.name}}">{{ year.name }}</h5>
  <ul>
  {% for post in year.items%}
  {% assign authors = post.authors | split:"," %}
  {% capture myauthors %}{% for author in authors%}{% if author contains 'Rahul Gopinath' %}<b>Rahul Gopinath</b>{% else %}{{author}}{% endif %}{% if forloop.last == true %}{% else %}, {% endif %}{% endfor %}{% endcapture %}
  <li><a href="{{ BASE_PATH }}{{ post.url  }}">{{ post.title }}</a><br/>
  {{ myauthors}} <br/>
  {{ post.venue }} {{ post.date | date: "%Y"}}.</li>
  {% endfor %}
  </ul>
{% endfor %}
</div>


