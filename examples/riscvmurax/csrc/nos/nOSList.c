/*
 * Copyright (c) 2014-2016 Jim Tremblay
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 */

#define NOS_PRIVATE
#include "nOS.h"

#ifdef __cplusplus
extern "C" {
#endif

void nOS_AppendToList (nOS_List *list, nOS_Node *node)
{
    node->prev = list->tail;
    node->next = NULL;
    if (node->prev != NULL) {
        node->prev->next = node;
    }
    list->tail = node;
    if (list->head == NULL) {
        list->head = node;
    }
}

void nOS_RemoveFromList (nOS_List *list, nOS_Node *node)
{
    if (list->head == node) {
        list->head = node->next;
    }
    if (list->tail == node) {
        list->tail = node->prev;
    }
    if (node->prev != NULL) {
        node->prev->next = node->next;
    }
    if (node->next != NULL) {
        node->next->prev = node->prev;
    }
    node->prev = NULL;
    node->next = NULL;
}

void nOS_RotateList (nOS_List *list)
{
    if (list->head != NULL) {
        if (list->head->next != NULL) {
            list->head->prev = list->tail;
            list->tail->next = list->head;
            list->head = list->head->next;
            list->tail = list->tail->next;
            list->head->prev = NULL;
            list->tail->next = NULL;
        }
    }
}

void nOS_WalkInList (nOS_List *list, nOS_NodeHandler handler, void *arg)
{
    nOS_Node    *it = list->head;
    nOS_Node    *next;

    while (it != NULL) {
        next = it->next;
        handler(it->payload, arg);
        it = next;
    }
}

#ifdef __cplusplus
}
#endif
