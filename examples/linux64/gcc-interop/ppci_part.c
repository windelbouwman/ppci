/* Will call external function. */
int printf(const char *s, ...);

/* Will access external data symbol. */
extern const char msg[];

/* Put external symbol in an array, to make sure that relocations for data
   section are properly generated. */
const char *msg_arr[] = {msg};

int ppci_func(void) {
    printf(msg);
    printf(msg_arr[0]);
}
