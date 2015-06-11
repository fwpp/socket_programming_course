from django.db import models
from decimal import Decimal

# Create your models here.

class User(models.Model):
	account = models.CharField(max_length=20)
	password = models.CharField(max_length=50)
	created_at = models.DateTimeField(auto_now_add=True)
	
class Post(models.Model):
	title = models.CharField(max_length=50)
	content = models.TextField()
	author= models.TextField(max_length=20)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)