---
published: true
title: Mutation 2016 at Chicago
layout: post
comments: true
tags: [mutation]
categories : post
---
[Mutation 2016](https://sites.google.com/site/mutation2016/mutation-2016), will be held at Chicago IL and is Co-Located with ICST 2016 (April 10 2016). Accepted papers will be published as part of the ICST proceedings.

Papers are due on January 15 2016. They can be 

* Full papers (10 pages) for research
* Short papers (6pages) for in progress,  tools, new ideas, problem descriptions, experience reports etc.
* Industrial papers (6 pages).

<script>
var url = "https://github.com/rahulgopinath/rahulgopinath.github.io/issues/" + "14"
var api_url = "https://api.github.com/repos/rahulgopinath/rahulgopinath.github.io/issues/" + "14" + "/comments"

$(document).ready(function () {
    $.ajax(api_url, {
        headers: {Accept: "application/vnd.github.v3.html+json"},
        dataType: "json",
        success: function(comments) {
            $("#gh-comments-list").append("Visit the <b><a href='" + url + "'>Github Issue</a></b> to comment on this post");
            $.each(comments, function(i, comment) {

                var date = new Date(comment.created_at);

                var t = "<div id='gh-comment'>";
                t += "<img src='" + comment.user.avatar_url + "' width='24px'>";
                t += "<b><a href='" + comment.user.html_url + "'>" + comment.user.login + "</a></b>";
                t += " posted at ";
                t += "<em>" + date.toUTCString() + "</em>";
                t += "<div id='gh-comment-hr'></div>";
                t += comment.body_html;
                t += "</div>";
                $("#gh-comments-list").append(t);
            });
        },
        error: function() {
            $("#gh-comments-list").append("Comments are not open for this post yet.");
        }
    });
});
</script>
