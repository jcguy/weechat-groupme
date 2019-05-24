import json
import requests
import weechat

from StringIO import StringIO

SCRIPT_NAME = 'groupme'
SCRIPT_AUTHOR = 'Corder Guy'
SCRIPT_VER = '0.0.1'
SCRIPT_LIC = 'MIT'
SCRIPT_DESC = 'Adds a groupme group as a buffer'

GROUPME_API_KEY = ''
GROUPME_BASE_URL = 'https://api.groupme.com/v3'

BUFFER_NAME = 'groupme'

script_options = {
    'groupmekey': '',
}


class GroupMe:
    def __init__(self):
        self.groups = []

    def join(self, num):
        self.groups[num].enable()

    def api_get(self, endpoint, payload):
        r = requests.get(
            GROUPME_BASE_URL + endpoint + '?token=' + GROUPME_API_KEY,
            params=payload)
        return r.content

    def get_groups(self):
        payload = None
        groups = json.loads(self.api_get('/groups', payload))[u'response']
        self.groups = [Group(g) for g in groups]

    def print_groups(self):
        weechat.prnt(get_main_buffer(), '-' * 20)
        weechat.prnt(get_main_buffer(), 'Current groups:')
        weechat.prnt(get_main_buffer(), '-' * 20)
        self.get_groups()
        for i, group in enumerate(self.groups):
            weechat.prnt(get_main_buffer(),
                         '(%d)\t%s' % (i, group.name.encode('utf-8')))


groupme = GroupMe()


def buffer_input_cb(data, buffer, input_data):
    if buffer == get_main_buffer():
        weechat.prnt(get_main_buffer(), '> ' + input_data)
        text = input_data.split(' ')
        if text[0] == 'list':
            groupme.print_groups()
        elif text[0] == 'join':
            if len(text) < 2:
                weechat.prnt(get_main_buffer(), 'Usage: join {#}')
            else:
                groupme.join(int(text[1]))
        return weechat.WEECHAT_RC_OK

    group = [g for g in groupme.groups if g.buffer == buffer][0]
    group.send_message(input_data)
    return weechat.WEECHAT_RC_OK


def buffer_close_cb(data, buffer):
    if buffer == get_main_buffer:
        [g.disable() for g in groupme.groups]
        return weechat.WEECHAT_RC_OK

    group = [g for g in groupme.groups if g.buffer == buffer][0]
    weechat.prnt(get_main_buffer(), group.name + ' closed')
    return weechat.WEECHAT_RC_OK


def config_cb(data, option, value):
    global GROUPME_API_KEY
    if option == 'groupmekey':
        GROUPME_API_KEY = value
    return weechat.WEECHAT_RC_OK


class Group:
    def __init__(self, json_obj):
        self.buffer = ''
        self.json_obj = json_obj
        self.id = self.json_obj[u'id']
        self.name = self.json_obj[u'name']
        self.description = self.json_obj[u'description']
        self.enabled = False

    def send_message(self, message):
        pass

    def populate(self):
        messages = json.loads(
            groupme.api_get('/groups/%s/messages' % self.id,
                            {'limit': '50'}))[u'response'][u'messages']
        for message in reversed(messages):
            text = message[u'name'].encode('utf-8') + '\t'

            if message[u'text']:
                text += message[u'text'].encode('utf-8')
                text += ' '

            if message[u'attachments']:
                images = []
                for attachment in message[u'attachments']:
                    if attachment[u'type'] == u'image':
                        images.append(attachment[u'url'])
                if len(images) > 0:
                    for image in images:
                        text += '%s ' % image.encode('utf-8')

            weechat.prnt(self.buffer, text)

    def enable(self):
        if self.enabled:
            return

        self.enabled = True

        self.buffer = (weechat.buffer_search('', '%s.%s' %
                                             (BUFFER_NAME, self.name))
                       or weechat.buffer_new(
                           '%s.%s' % (BUFFER_NAME, self.name),
                           'buffer_input_cb', '', 'buffer_close_cb', ''))
        weechat.buffer_set(self.buffer, 'title',
                           self.name + ': ' + self.description)

        self.populate()

    def disable(self):
        self.enabled = False


def get_main_buffer():
    buffer = (weechat.buffer_search('', 'server.%s' % BUFFER_NAME) or
              weechat.buffer_new('server.%s' % BUFFER_NAME, 'buffer_input_cb',
                                 '', 'buffer_close_cb', ''))
    weechat.buffer_set(buffer, 'title', 'GroupMe server buffer')
    weechat.buffer_set(buffer, 'localvar_set_no_log', '1')

    return buffer


def init():
    weechat.register(SCRIPT_NAME, SCRIPT_AUTHOR, SCRIPT_VER, SCRIPT_LIC,
                     SCRIPT_DESC, '', '')

    weechat.hook_config('plugins.var.python.' + SCRIPT_NAME + '.*',
                        'config_cb', '')
    for option, default_value in script_options.items():
        if not weechat.config_is_set_plugin(option):
            weechat.config_set_plugin(option, default_value)

    global GROUPME_API_KEY
    GROUPME_API_KEY = weechat.config_string(
        weechat.config_get(
            'plugins.var.python.' + SCRIPT_NAME + '.groupmekey'))

    get_main_buffer()


def main():
    init()
    groupme.get_groups()


if __name__ == '__main__':
    main()

