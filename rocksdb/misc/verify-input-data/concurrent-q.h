#pragma once

#include <queue>
#include <mutex>


class ConQEmpty {
};


template <typename T>
class ConcurrentQ {
private:
	std::queue<T> _q;
	std::mutex _q_lock;

public:
	ConcurrentQ() {
	}

	virtual ~ConcurrentQ() {
	}

	T Pop() {
		std::lock_guard<std::mutex> _(_q_lock);
		if (_q.empty())
			throw ConQEmpty();
		T e = _q.front();
		_q.pop();
		return e;
	}

	void Push(const T& e) {
		std::lock_guard<std::mutex> _(_q_lock);
		_q.push(e);
	}

	size_t Size() {
		std::lock_guard<std::mutex> _(_q_lock);
		return _q.size();
	}
};
