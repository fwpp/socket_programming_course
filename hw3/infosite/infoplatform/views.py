from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Q
from infoplatform.models import User, Post
import hashlib
import json
import datetime

# Create your views here.

def login(request):
	auth_check = auth(request)
	if auth_check:
		return main(request)
	else:
		return render(request,
					  'login.html')

def login_check(request):
	account = request.POST['account']
	password = request.POST['password']
	
	md5Hash = hashlib.md5()
	md5Hash.update( (password+'post_board').encode('utf-8') )
	password = md5Hash.hexdigest()
	
	check_data = User.objects.filter(account=account)
	if len(check_data) == 1:
		if check_data[0].password == password:
			posts = Post.objects.all().order_by('-updated_at')
			response = render(request,
						      'main.html',
						      {'posts': posts})
			response.set_cookie('account',account)
			return response
			
	return render(request,
				  'login.html',
				  {'error': 'Error: account or password is wrong'})

def logout(request):
	response = render(request,
					  'login.html')
	response.delete_cookie('account')
	return response
				  
def register(request):
	return render(request,
				  'register.html')
				  
def user_create(request):
	account = request.POST['account']
	password = request.POST['password']
	
	md5Hash = hashlib.md5()
	md5Hash.update( (password+'post_board').encode('utf-8') )
	password = md5Hash.hexdigest()
	User.objects.create(account=account, password=password)
	return render(request,
				  'login.html')

def auth(request):
	if 'account' in request.COOKIES:
		return request.COOKIES['account']
	else:
		return None
				  
def main(request):
	auth_check = auth(request)
	if auth_check == None:
		return render(request,
					  'login.html')
	posts = Post.objects.all().order_by('-updated_at')
	return render(request,
				  'main.html',
				  {'posts': posts})
				  
def post_create(request):
	auth_check = auth(request)
	if auth_check ==  None:
		return render(request,
					  'login.html')

	account = auth_check
	title = request.POST['title']
	content = request.POST['content']
	Post.objects.create(title=title,content=content,author=account)
	return main(request)

def profile(request):
	auth_check = auth(request)
	if auth_check ==  None:
		return render(request,
					  'login.html')
					  
	account = auth_check
	user = User.objects.get(account=account)
	return render(request,
				  'profile.html',
				  {'user':user})
				  
def profile_update(request):
	auth_check = auth(request)
	if auth_check ==  None:
		return render(request,
					  'login.html')
	
	account = auth_check
	user = User.objects.get(account=account)
	
	password = request.POST['password']
	
	md5Hash = hashlib.md5()
	md5Hash.update( (password+'post_board').encode('utf-8') )
	password = md5Hash.hexdigest()

	user.password = password
	user.save()
	
	return main(request)

def ajax_check_new_post(request):
	auth_check = auth(request)
	if auth_check ==  None:
		return render(request,
					  'login.html')

	data = { 'change' : False, 'amount' : 0 }
	oldTime = request.GET['oldTime'][:10]
	oldTime = datetime.datetime.fromtimestamp( int(oldTime) + 1 )
	
	post_data = Post.objects.filter( updated_at__gt=oldTime )
	if len(post_data) != 0:
		data['change'] = True
		data['amount'] = len(post_data)
	jdata = json.dumps(data)
	
	return HttpResponse(jdata, content_type="application/json")

def search_post(request):
	searchItem = request.POST['search']
	posts = Post.objects.all().filter( Q(author__contains=searchItem) | Q(title__contains=searchItem) | Q(content__contains=searchItem) )
	return render(request,
				  'main.html',
				  {'posts': posts})
	