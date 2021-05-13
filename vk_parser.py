import vk_api
import pickle
import time
import json


# two factor auth
def auth_handler():
    key = input("Enter authentication code: ")
    remember_device = True
    return key, remember_device

# login to VK API
login, password = 'login', 'password'
vk_session = vk_api.VkApi(login=login, password=password, auth_handler=auth_handler)
vk_session.auth(token_only=True)
vk = vk_session.get_api()
tools = vk_api.VkTools(vk_session)

# GROUP_ID = str(-197654594)

# IDs of analysed groups
GROUP_IDS = ['-192608132', '-192710341', '-203598592', '-185593520', '-197654594']

# View total amount of posts among all groups
comment_counter = 0
for i in GROUP_IDS:
    wall_posts = tools.get_all('wall.get', 100, {'owner_id': i})
    comment_counter += wall_posts['count']
print('Total posts:', comment_counter)


final_data_to_dump = []

for group_id in GROUP_IDS:

    # get all posts from the group
    # count = total number of posts
    # items = posts itself with data
    wall_posts = tools.get_all('wall.get', 100, {'owner_id': group_id})
    wall_post_count = wall_posts['count']
    print('Id:', group_id, '\n', 'Posts: ', wall_post_count)

    post_number = 0

    # create empty json file in directory
    # after it will rewrite itself multiple times
    with open(f'comments_{group_id}.json', 'w', encoding='utf-8') as jc:
        json.dump([{1:1}], jc)

    for post in wall_posts['items']:

        # count posts and print
        post_number += 1
        print("Post: ", post_number, '/', wall_post_count)

        # get comments for the current post
        post_comments = tools.get_all('wall.getComments', 100, {'owner_id': group_id, 'post_id': post['id']})
        post_comments_count = post_comments['count']
        comments_items = post_comments['items']

        post_comment_users_info = []
        comments_ids = []

        for comment in comments_items:

            # delete useless attachments
            comment['attachments'] = ''

            # avoid comments from deleted profiles and groups
            if ('deleted' in comment.keys()) or (str(comment['from_id'])[0] == '-'):
                post_comment_users_info.append('')
            else:
                # collect user data
                user_info = vk.users.get(user_id=comment['from_id'], fields="sex, bdate, city, personal")
                post_comment_users_info.append(user_info[0])
            comments_ids.append(comment['id'])

        # append user data to comments items
        for i in range(len(comments_items)):
            comments_items[i].update(post_comment_users_info[i])

        # final comments = comments + thread comments
        all_comments = []
        all_comments += comments_items

        # collect comments from threads
        for i in comments_ids:
            thread_comments_items = []

            # for every comment get thread comments
            post_thread_comments = tools.get_all('wall.getComments', 100, {'owner_id': group_id, 'post_id': post['id'], 'comment_id': i})
            thread_comments_items += post_thread_comments['items']

            thread_comment_users_info = []

            for thread_comment in thread_comments_items:

                # delete useless attachs
                thread_comment['attachments'] = ''

                # avoid comments from deleted profiles and groups
                if ('deleted' in thread_comment.keys()) or (str(thread_comment['from_id'])[0] == '-'):
                    thread_comment_users_info.append('')
                else:
                    # collect user data
                    user_info = vk.users.get(user_id=thread_comment['from_id'], fields="sex, bdate, city, personal")
                    thread_comment_users_info.append(user_info[0])

            # append user data to comments
            for j in range(len(thread_comments_items)):
                thread_comments_items[j].update(thread_comment_users_info[j])

            all_comments += thread_comments_items

        final_data_to_dump += all_comments

        print("Total comments: ", len(final_data_to_dump))

        # sleep to avoid vk api ban
        time.sleep(2)

        # fill data[] with previous json file
        data = []
        with open(f'comments_{group_id}.json', 'r', encoding='utf-8') as f:
            d = json.load(f)
            data.extend(d)

        # append comments to data[]
        for i in final_data_to_dump:
            data.extend([i])

        # clear final[] and write everything to new json file
        final_data_to_dump = []
        with open(f'comments_{group_id}.json', 'w',  encoding='utf-8') as jc:
            json.dump(data, jc, ensure_ascii=False)

