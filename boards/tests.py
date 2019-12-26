from django.test import TestCase
from django.urls import resolve, reverse
from django.contrib.auth.models import User
from django import forms
from .views import home, board_topics, new_topic, topic_posts, reply_topic
from .models import Board, Topic, Post
from .forms import NewTopicForm, PostForm
from .templatetags.form_tags import field_type, input_class

# Create your tests here.
class HomeTests(TestCase):
	def setUp(self):
		self.board = Board.objects.create(name='Django', description='Django board.')
		url = reverse('home')
		self.response = self.client.get(url)

	def test_home_view_status_code(self):
		self.assertEquals(self.response.status_code, 200)

	def test_home_url_resolves_home_view(self):
		view = resolve('/')
		self.assertEquals(view.func, home)

	def test_home_view_contains_link_to_topics_page(self):
		board_topics_url = reverse('board_topics', kwargs={'pk': self.board.pk})
		self.assertContains(self.response, 'href="{0}"'.format(board_topics_url))


class BoardTopicsTests(TestCase):
	def setUp(self):
		Board.objects.create(name='Django', description='Django board.')

	def test_board_topics_view_success_status_code(self):
		url = reverse('board_topics', kwargs={'pk': 1})
		response = self.client.get(url)
		self.assertEquals(response.status_code, 200)

	def test_board_topics_view_not_found_status_code(self):
		url = reverse('board_topics', kwargs={'pk': 99})
		response = self.client.get(url)
		self.assertEquals(response.status_code, 404)

	def test_board_topics_url_resolves_board_topics_view(self):
		view = resolve('/boards/1/')
		self.assertEquals(view.func, board_topics)
		
	def test_board_topics_view_contains_navigation_links(self):
		board_topics_url = reverse('board_topics', kwargs={'pk': 1})
		homepage_url = reverse('home')
		new_topic_url = reverse('new_topic', kwargs={'pk': 1})

		response = self.client.get(board_topics_url)

		self.assertContains(response, 'href="{0}"'.format(homepage_url))
		self.assertContains(response, 'href="{0}"'.format(new_topic_url))


class NewTopicTests(TestCase):
	def setUp(self):
		Board.objects.create(name='Django', description='Django board.')
		User.objects.create_user(username='john', email='john@doe.com', password='123')

	def test_new_topic_view_success_status_code(self):
		url = reverse('new_topic', kwargs={'pk': 1})
		response = self.client.get(url)
		self.assertEquals(response.status_code, 200)

	def test_new_topic_view_not_found_status_code(self):
		url = reverse('new_topic', kwargs={'pk': 99})
		response = self.client.get(url)
		self.assertEquals(response.status_code, 404)

	def test_new_topic_url_resolves_new_topic_view(self):
		view = resolve('/boards/1/new/')
		self.assertEquals(view.func, new_topic)

	def test_new_topic_view_contains_link_back_to_board_topics_view(self):
		new_topic_url = reverse('new_topic', kwargs={'pk': 1})
		board_topics_url = reverse('board_topics', kwargs={'pk': 1})
		response = self.client.get(new_topic_url)
		self.assertContains(response, 'href="{0}"'.format(board_topics_url))

	def test_csrf(self):
		url = reverse('new_topic', kwargs={'pk': 1})
		response = self.client.get(url)
		self.assertContains(response, 'csrfmiddlewaretoken')

	def test_new_topic_valid_post_data(self):
		url = reverse('new_topic', kwargs={'pk': 1})
		data = {
			'subject': 'Test title',
			'message': 'Lorem ipsum dolor sit amet'
		}
		response = self.client.post(url, data)
		self.assertTrue(Topic.objects.exists())
		self.assertTrue(Post.objects.exists())

	def test_new_topic_invalid_post_data(self):
		'''
		Invalid post data should not redirect
		The expected behavior is to show the form again with validation errors
		'''
		url = reverse('new_topic', kwargs={'pk': 1})
		response = self.client.post(url, {})
		self.assertEquals(response.status_code, 200)

	def test_new_topic_invalid_post_data_empty_fields(self):
		'''
		Invalid post data should not redirect
		The expected behavior is to show the form again with validation errors
		'''
		url = reverse('new_topic', kwargs={'pk': 1})
		data = {
			'subject': '',
			'message': ''
		}
		response = self.client.post(url, data)
		self.assertEquals(response.status_code, 200)
		self.assertFalse(Topic.objects.exists())
		self.assertFalse(Post.objects.exists())

	def test_contains_form(self):  # <- new test
		url = reverse('new_topic', kwargs={'pk': 1})
		response = self.client.get(url)
		form = response.context.get('form')
		self.assertIsInstance(form, NewTopicForm)

	def test_new_topic_invalid_post_data(self):  # <- updated this one
		'''
		Invalid post data should not redirect
		The expected behavior is to show the form again with validation errors
		'''
		url = reverse('new_topic', kwargs={'pk': 1})
		response = self.client.post(url, {})
		form = response.context.get('form')
		self.assertEquals(response.status_code, 200)
		self.assertTrue(form.errors)

class ExampleForm(forms.Form):
    name = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput())
    class Meta:
        fields = ('name', 'password')

class FieldTypeTests(TestCase):
    def test_field_widget_type(self):
        form = ExampleForm()
        self.assertEquals('TextInput', field_type(form['name']))
        self.assertEquals('PasswordInput', field_type(form['password']))

class InputClassTests(TestCase):
    def test_unbound_field_initial_state(self):
        form = ExampleForm()  # unbound form
        self.assertEquals('form-control ', input_class(form['name']))

    def test_valid_bound_field(self):
        form = ExampleForm({'name': 'john', 'password': '123'})  # bound form (field + data)
        self.assertEquals('form-control is-valid', input_class(form['name']))
        self.assertEquals('form-control ', input_class(form['password']))

    def test_invalid_bound_field(self):
        form = ExampleForm({'name': '', 'password': '123'})  # bound form (field + data)
        self.assertEquals('form-control is-invalid', input_class(form['name']))

class TopicPostsTests(TestCase):
    def setUp(self):
        board = Board.objects.create(name='Django', description='Django board.')
        user = User.objects.create_user(username='john', email='john@doe.com', password='123')
        topic = Topic.objects.create(subject='Hello, world', board=board, starter=user)
        Post.objects.create(message='Lorem ipsum dolor sit amet', topic=topic, created_by=user)
        url = reverse('topic_posts', kwargs={'pk': board.pk, 'topic_pk': topic.pk})
        self.response = self.client.get(url)

    def test_status_code(self):
        self.assertEquals(self.response.status_code, 200)

    def test_view_function(self):
        view = resolve('/boards/1/topics/1/')
        self.assertEquals(view.func, topic_posts)

class ReplyTopicTestCase(TestCase):
    '''
    Base test case to be used in all `reply_topic` view tests
    '''
    def setUp(self):
        self.board = Board.objects.create(name='Django', description='Django board.')
        self.username = 'john'
        self.password = '123'
        user = User.objects.create_user(username=self.username, email='john@doe.com', password=self.password)
        self.topic = Topic.objects.create(subject='Hello, world', board=self.board, starter=user)
        Post.objects.create(message='Lorem ipsum dolor sit amet', topic=self.topic, created_by=user)
        self.url = reverse('reply_topic', kwargs={'pk': self.board.pk, 'topic_pk': self.topic.pk})


class LoginRequiredReplyTopicTests(ReplyTopicTestCase):
    def test_redirection(self):
        login_url = reverse('login')
        response = self.client.get(self.url)
        self.assertRedirects(response, '{login_url}?next={url}'.format(login_url=login_url, url=self.url))


class ReplyTopicTests(ReplyTopicTestCase):
    def setUp(self):
        super().setUp()
        self.client.login(username=self.username, password=self.password)
        self.response = self.client.get(self.url)

    def test_status_code(self):
        self.assertEquals(self.response.status_code, 200)

    def test_view_function(self):
        view = resolve('/boards/1/topics/1/reply/')
        self.assertEquals(view.func, reply_topic)

    def test_csrf(self):
        self.assertContains(self.response, 'csrfmiddlewaretoken')

    def test_contains_form(self):
        form = self.response.context.get('form')
        self.assertIsInstance(form, PostForm)

    def test_form_inputs(self):
        '''
        The view must contain two inputs: csrf, message textarea
        '''
        self.assertContains(self.response, '<input', 1)
        self.assertContains(self.response, '<textarea', 1)


class SuccessfulReplyTopicTests(ReplyTopicTestCase):
    def setUp(self):
        super().setUp()
        self.client.login(username=self.username, password=self.password)
        self.response = self.client.post(self.url, {'message': 'hello, world!'})

    def test_redirection(self):
        '''
        A valid form submission should redirect the user
        '''
        topic_posts_url = reverse('topic_posts', kwargs={'pk': self.board.pk, 'topic_pk': self.topic.pk})
        self.assertRedirects(self.response, topic_posts_url)

    def test_reply_created(self):
        '''
        The total post count should be 2
        The one created in the `ReplyTopicTestCase` setUp
        and another created by the post data in this class
        '''
        self.assertEquals(Post.objects.count(), 2)


class InvalidReplyTopicTests(ReplyTopicTestCase):
    def setUp(self):
        '''
        Submit an empty dictionary to the `reply_topic` view
        '''
        super().setUp()
        self.client.login(username=self.username, password=self.password)
        self.response = self.client.post(self.url, {})

    def test_status_code(self):
        '''
        An invalid form submission should return to the same page
        '''
        self.assertEquals(self.response.status_code, 200)

    def test_form_errors(self):
        form = self.response.context.get('form')
        self.assertTrue(form.errors)