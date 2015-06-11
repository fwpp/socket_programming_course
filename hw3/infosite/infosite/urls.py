from django.conf.urls import patterns, include, url
from django.contrib import admin

from infoplatform.views import login, login_check, register, user_create, post_create, logout, profile, profile_update, ajax_check_new_post, search_post

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'infosite.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
	
	url(r'^$', login),
	url(r'^login_check/$', login_check),
	url(r'^register/$', register),
	url(r'^register/user_create/$', user_create),
	url(r'^main/post_create/$', post_create),
	url(r'^main/logout/$', logout),
	url(r'^main/profile/$', profile),
	url(r'^main/profile_update/$', profile_update),
	url(r'^main/ajax_check_new_post/$', ajax_check_new_post),
	url(r'^main/search_post/$', search_post),
)
